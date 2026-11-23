param(
    [ValidateRange(1024, 65535)][int]$Port = 18881,
    [string]$DockerConfig = ''
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $OutputEncoding
$repo = Split-Path -Parent $PSScriptRoot
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
try { $listener.Start() } finally { $listener.Stop() }
$runId = 'coffeehub-demo-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
$runRoot = Join-Path ([System.IO.Path]::GetTempPath()) $runId
New-Item -ItemType Directory -Path $runRoot | Out-Null
$clientArgs = @()
if ($DockerConfig) { $clientArgs = @('--config', $DockerConfig) }
function New-LocalSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
}

# Copy tracked source only: never send local .env, keys, venv or node_modules.
$tracked = & git -C $repo -c core.quotepath=false ls-files -- backend frontend
if ($LASTEXITCODE -ne 0) { throw 'Cannot read tracked project source.' }
foreach ($relative in $tracked) {
    $destination = Join-Path $runRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination $destination
}
foreach ($directory in @('database', 'fixtures')) {
    New-Item -ItemType Directory -Path (Join-Path $runRoot $directory) | Out-Null
}
foreach ($name in @('init.sql', 'seed.sql')) {
    Copy-Item -LiteralPath (Join-Path $repo "database/$name") -Destination (Join-Path $runRoot "database/$name")
}
foreach ($name in @('nginx.local.conf', 'nginx.demo.conf')) {
    Copy-Item -LiteralPath (Join-Path $repo "frontend/$name") -Destination (Join-Path $runRoot "fixtures/$name")
}
$envFile = Join-Path $runRoot 'demo.env'
$values = @{
    PHASE1_RUN_ID = $runId
    PHASE1_ATTEMPT = '1'
    PHASE1_MYSQL_PASSWORD = New-LocalSecret
    PHASE1_JWT_KEY = New-LocalSecret
    PHASE1_BUILD_CONTEXT = (Join-Path $runRoot 'backend').Replace('\', '/')
    PHASE1_SQL_DIR = (Join-Path $runRoot 'database').Replace('\', '/')
    PHASE1_FIXTURE_DIR = (Join-Path $runRoot 'fixtures').Replace('\', '/')
    PHASE2_FRONTEND_CONTEXT = (Join-Path $runRoot 'frontend').Replace('\', '/')
    PHASE2_PORT = "$Port"
}
[System.IO.File]::WriteAllLines($envFile, @($values.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }), $OutputEncoding)
$stateFile = Join-Path $runRoot 'state.json'
@{ repo = $repo; root = $runRoot; project = $runId; env_file = $envFile; port = $Port } |
    ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding UTF8
$existing = & docker @clientArgs volume ls --format '{{.Name}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker is unavailable.' }
if ($existing -contains "${runId}_phase1_mysql_1" -or $existing -contains "${runId}_local_gcs") {
    throw 'Refuse to initialize an existing volume.'
}
$composeArgs = @('compose', '-p', $runId, '--env-file', $envFile,
    '-f', (Join-Path $repo 'docker-compose.integration.yml'),
    '-f', (Join-Path $repo 'docker-compose.local.yml'),
    '-f', (Join-Path $repo 'docker-compose.demo.yml'))
# Windows PowerShell treats Docker's normal stderr progress as error records
# when output is redirected. Judge startup by Docker's exit code instead.
$previousPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & docker @clientArgs @composeArgs up -d --build --wait --wait-timeout 90
    $startupExit = $LASTEXITCODE
} finally { $ErrorActionPreference = $previousPreference }
if ($startupExit -ne 0) { throw "Startup failed; resources retained. State: $stateFile" }

# One-time initialization, inside the newly created container. Refuse existing data.
$initialize = @'
import asyncio, os, json
from pathlib import Path
import asyncmy, httpx

def statements(sql):
    sql = '\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
    start = 0; quote = None; i = 0
    while i < len(sql):
        char = sql[i]
        if quote:
            if char == '\\': i += 2; continue
            if char == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote: i += 2; continue
                quote = None
        elif char in '\'"`': quote = char
        elif char == ';':
            if sql[start:i].strip(): yield sql[start:i]
            start = i + 1
        i += 1
    if sql[start:].strip(): yield sql[start:]

async def main():
    assert os.environ['PHASE1_RUN_ID'].startswith('coffeehub-demo-')
    assert os.environ['APP_ENV'] == 'test' and os.environ['DB_HOST'] == '127.0.0.1'
    assert os.environ['DB_PORT'] == '33381' and os.environ['STORAGE_EMULATOR_HOST'] == 'http://gcs:4443'
    db = await asyncmy.connect(host='127.0.0.1', port=33381, user='root', password=os.environ['DB_PASSWORD'], charset='utf8mb4', autocommit=True)
    async with db.cursor() as cursor:
        await cursor.execute('SELECT @@datadir')
        assert (await cursor.fetchone())[0].rstrip('/') == '/var/lib/mysql/coffeehub-batch3-phase1'
        await cursor.execute('SHOW DATABASES')
        assert {row[0] for row in await cursor.fetchall()} <= {'mysql','sys','information_schema','performance_schema','coffeehub_phase1'}, 'Existing database: initialization refused'
        await cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='coffeehub_phase1'")
        assert (await cursor.fetchone())[0] == 0
        for name in ('init.sql', 'seed.sql'):
            for statement in statements(Path('/database', name).read_text(encoding='utf-8')):
                await cursor.execute(statement)
        for table, count in {'users':30,'products':20,'orders':30,'order_items':32}.items():
            await cursor.execute('SELECT COUNT(*) FROM ' + table)
            assert (await cursor.fetchone())[0] == count
    db.close()
    async with httpx.AsyncClient(base_url='http://gcs:4443') as client:
        response = await client.post('/storage/v1/b', json={'name':'coffeehub-local-images'})
        assert response.status_code in (200,201)
    print('Original seed loaded once; no existing database or volume was overwritten.')

try:
    asyncio.run(main())
except Exception as error:
    print('Initialization stopped:', type(error).__name__)
    raise SystemExit(1)
'@
try {
    $ErrorActionPreference = 'Continue'
    $initialize | & docker @clientArgs @composeArgs exec -T backend python -
    $initializationExit = $LASTEXITCODE
} finally { $ErrorActionPreference = $previousPreference }
if ($initializationExit -ne 0) { throw "Initialization failed; do not reset existing data. State: $stateFile" }
Write-Output "Local demo: http://localhost:$Port"
Write-Output "State file: $stateFile"
Write-Output 'Keep the state/env files private. No cloud credentials are used.'
