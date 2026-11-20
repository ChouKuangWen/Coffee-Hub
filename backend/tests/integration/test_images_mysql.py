"""Batch 5：真實隔離 MySQL＋記憶體 GCS 替身；不是實際 GCS 整合驗證。"""
import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock

import httpx
import pytest
from PIL import Image
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tests.unit.test_account_permissions import isolated_app, csrf_client


class FakeGCS:
    def __init__(self):
        self.objects = {}
        self.generation = 0
        self.deletes = []
        self.fail_upload_after_store = False
        self.fail_delete_once = set()

    def upload_bytes(self, bucket, key, contents, content_type, image_id, sha256):
        assert (bucket, key) not in self.objects
        self.generation += 1
        self.objects[bucket, key] = {'generation': self.generation,
            'metadata': {'coffeehub_image_id': image_id, 'sha256': sha256}, 'held': False}
        if self.fail_upload_after_store:
            raise OSError('simulated lost upload response')
        return self.generation

    def inspect_object(self, bucket, key):
        return self.objects.get((bucket, key))

    def delete_generation(self, bucket, key, generation):
        if key in self.fail_delete_once:
            self.fail_delete_once.remove(key)
            raise OSError('simulated transient delete failure')
        assert self.objects[bucket, key]['generation'] == generation
        self.deletes.append((bucket, key, generation))
        del self.objects[bucket, key]


@pytest.mark.skipif(not os.getenv('COFFEEHUB_TEST_MYSQL_URL'), reason='未指定隔離 MySQL')
def test_images_mysql(isolated_app, monkeypatch):
    asyncio.run(_scenario(isolated_app, monkeypatch))


async def _scenario(env, monkeypatch):
    from app.models.users import Users
    from app.models.roles import Roles
    from app.models.products import Products
    from app.models.image_asset import ImageAsset
    from app.services import image_service, product_service
    from app.core.security import hash_password

    url = make_url(os.environ['COFFEEHUB_TEST_MYSQL_URL'])
    expected = Path(os.environ['COFFEEHUB_TEST_MYSQL_DATADIR'])
    assert url.host in ('localhost','127.0.0.1') and url.port not in (None,3306,3307)
    assert expected.name.startswith(('coffeehub-batch3-', 'coffeehub-batch5-'))
    name = 'coffeehub_batch5_' + uuid4().hex
    bootstrap = create_async_engine(url.set(database=None))
    try:
        async with bootstrap.begin() as conn:
            assert Path((await conn.execute(text('SELECT @@datadir'))).scalar_one()).resolve() == expected.resolve()
            await conn.execute(text(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4'))
            await conn.execute(text(f'CREATE DATABASE `{name}_fresh` CHARACTER SET utf8mb4'))
    finally:
        await bootstrap.dispose()
    engine = create_async_engine(url.set(database=name))
    fresh = create_async_engine(url.set(database=name + '_fresh'))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def get_db():
        async with sessions() as db:
            yield db

    env.app.dependency_overrides[env.get_db] = get_db
    env.app.state.limiter.enabled = False
    fake = FakeGCS()
    monkeypatch.setattr(image_service, 'gcs_storage', fake)
    now = [datetime.now(timezone.utc).replace(tzinfo=None)]
    monkeypatch.setattr(image_service, '_now', lambda: now[0])
    for key, value in {'APP_ENV':'test', 'IMAGE_STORAGE_ENABLED':True, 'GCS_IMAGE_BUCKET':'coffeehub-test-only',
                       'IMAGE_DELETE_ENABLED':False}.items():
        monkeypatch.setattr(image_service.settings, key, value, raising=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: Users.metadata.create_all(c,
                tables=[table for key, table in Users.metadata.tables.items() if key != 'image_assets']))
            for migration in ('001_account_lifecycle.sql','002_simulated_checkout.sql','003_order_lifecycle.sql','004_image_assets.sql','004_image_assets.sql'):
                script = Path('../database/migrations', migration).read_text(encoding='utf-8')
                script = '\n'.join(line for line in script.splitlines() if not line.lstrip().startswith('--'))
                for statement in script.split(';'):
                    if statement.strip():
                        await conn.execute(text(statement))
            assert (await conn.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='004_image_assets'"))).scalar_one() == 1
        async with fresh.begin() as conn:
            script = Path('../database/init.sql').read_text(encoding='utf-8')
            script = '\n'.join(line for line in script.splitlines() if not line.lstrip().startswith('--'))
            for statement in script.split(';'):
                match = re.match(r'\s*CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)', statement, re.I)
                if match and match[1] in {'roles','users','products','image_assets'}:
                    await conn.execute(text(statement))
        async with engine.connect() as old, fresh.connect() as new:
            for query in (
                "SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA FROM information_schema.columns WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='image_assets' ORDER BY ORDINAL_POSITION",
                "SELECT INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME FROM information_schema.statistics WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='image_assets' ORDER BY INDEX_NAME,SEQ_IN_INDEX",
                "SELECT COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.key_column_usage WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='image_assets' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY COLUMN_NAME",
            ):
                assert (await old.execute(text(query))).all() == (await new.execute(text(query))).all()
        async with sessions() as db:
            db.add_all([Roles(role_id=i,name=n) for i,n in [(1,'Admin'),(2,'Seller'),(3,'Customer')]])
            await db.flush()
            for i,n,role in [(1,'admin',1),(2,'s1',2),(3,'s2',2),(4,'buyer',3)]:
                db.add(Users(user_id=i,username=n,email=f'{n}@example.com',phone='0',address='test',role_id=role,
                             password_hash=hash_password('test-only-value')))
            await db.commit()
        print('PASS image migration 004 rerun / fresh-upgrade columns, indexes and FKs')

        def client():
            return csrf_client(env.app)

        def check(response, status=200):
            assert response.status_code == status, (response.status_code,response.text)
            return response.json() if response.content else None

        content = BytesIO()
        Image.new('RGB',(20,15),'red').save(content,format='PNG')
        png = content.getvalue()

        async def asset(image_id):
            async with sessions() as db:
                return await db.get(ImageAsset,image_id)

        async with client() as admin, client() as s1, client() as s2, client() as buyer, client() as visitor:
            for c,n in [(admin,'admin'),(s1,'s1'),(s2,'s2'),(buyer,'buyer')]:
                check(await c.post('/auth/login',data={'username':f'{n}@example.com','password':'test-only-value'}))
            p1=check(await s1.post('/products/',json={'name':'one','price':'10','stock':10}),201)
            p2=check(await s2.post('/products/',json={'name':'two','price':'20','stock':10}),201)

            async def upload(c=s1, pid=p1['product_id'], data=png, mime='image/png'):
                return await c.post('/upload/',data={'product_id':str(pid)},files={'file':('../../unsafe.svg',data,mime)})

            check(await upload(visitor),401)
            check(await upload(buyer),403)
            check(await upload(s2),403)
            assert not fake.objects
            check(await upload(data=b'<svg>pretend image</svg>'),415)
            check(await upload(data=b'x'*(5*1024*1024+1)),413)
            check(await upload(mime='image/jpeg'),415)
            old=check(await upload())
            assert old['filename'].endswith('.png') and '/' not in old['filename']
            check(await s1.patch(f"/products/{p1['product_id']}",json={'main_image':old['image_url']}))
            check(await s2.patch(f"/products/{p2['product_id']}",json={'main_image':old['image_url']}),403)
            check(await s1.patch(f"/products/{p1['product_id']}",json={'main_image':'https://example.com/unverified.png'}),403)
            check(await s1.patch(f"/products/{p1['product_id']}",json={'sub_images':[old['image_url']]*4}),422)
            check(await s1.patch(f"/products/{p1['product_id']}",json={'sub_images':[old['image_url']]}),422)
            extra=[check(await upload()) for _ in range(3)]
            check(await s1.patch(f"/products/{p1['product_id']}",json={'sub_images':[i['image_url'] for i in extra]}))
            assert len(check(await s1.get(f"/products/{p1['product_id']}"))['sub_images'])==3
            # GCS 已寫入但回應遺失：只留下持久 uploading 候選，原圖不變。
            fake.fail_upload_after_store=True
            check(await upload(),502)
            fake.fail_upload_after_store=False
            async with sessions() as db:
                orphan=(await db.execute(select(ImageAsset).where(ImageAsset.state=='uploading'))).scalar_one()
                orphan_id=orphan.image_id
                assert (orphan.bucket,orphan.object_name) in fake.objects
            assert check(await s1.get(f"/products/{p1['product_id']}"))['main_image']==old['image_url']
            new=check(await upload())
            with monkeypatch.context() as patch:
                patch.setattr(product_service,'record_required_action',AsyncMock(side_effect=RuntimeError('audit unavailable')))
                check(await s1.patch(f"/products/{p1['product_id']}",json={'main_image':new['image_url']}),500)
            assert check(await s1.get(f"/products/{p1['product_id']}"))['main_image']==old['image_url']
            assert (await asset(old['image_id'])).cleanup_after is None
            assert (await asset(new['image_id'])).cleanup_after is not None
            # 上傳成功但 READY 審計／DB 階段失敗，亦必須留下可回收意圖。
            original_audit=image_service._audit

            async def fail_ready(db,request,actor_id,action,*args,**kwargs):
                if action=='IMAGE_UPLOAD_READY':
                    raise RuntimeError('ready audit unavailable')
                await original_audit(db,request,actor_id,action,*args,**kwargs)

            with monkeypatch.context() as patch:
                patch.setattr(image_service,'_audit',fail_ready)
                check(await upload(),502)
            assert check(await s1.get(f"/products/{p1['product_id']}"))['main_image']==old['image_url']
            check(await s1.patch(f"/products/{p1['product_id']}",json={'main_image':new['image_url']}))
            old_asset=await asset(old['image_id'])
            assert old_asset.cleanup_after>=now[0]+timedelta(days=7)
            old_key=(old_asset.bucket,old_asset.object_name)
            check(await admin.post('/upload/cleanup',json={'dry_run':False}),403)
            monkeypatch.setattr(image_service.settings,'IMAGE_DELETE_ENABLED',True)
            assert check(await admin.post('/upload/cleanup',json={'dry_run':False}))['candidates']==0
            assert old_key in fake.objects
            print('PASS upload and association authorization / spoof-size-count rejection / verified 1+3 images / failure preserves original / default delete gate / 7-day grace')

            # 模擬既有共享引用，即使其他商品已下架也不得清理。
            async with sessions() as db:
                other=await db.get(Products,p2['product_id'])
                other.main_image=old['image_url']
                other.is_active=False
                await db.commit()
            now[0]+=timedelta(days=8)
            check(await admin.post('/upload/cleanup',json={'dry_run':True}))
            assert fake.deletes==[]
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert old_key in fake.objects
            assert (await asset(orphan_id)).state=='deleted'
            assert (await asset(old['image_id'])).cleanup_after is None
            # 移除共享引用後重新計算安全期；保留標記亦必須阻擋刪除。
            check(await admin.patch(f"/products/{p2['product_id']}",json={'main_image':None}))
            async with sessions() as db:
                held=await db.get(ImageAsset,old['image_id'])
                held.is_held=True
                await db.commit()
            now[0]+=timedelta(days=8)
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert old_key in fake.objects
            async with sessions() as db:
                held=await db.get(ImageAsset,old['image_id'])
                held.is_held=False
                await db.commit()
            fake.fail_delete_once.add(old_key[1])
            assert check(await admin.post('/upload/cleanup',json={'dry_run':False}))['failed']>=1
            retry_asset=await asset(old['image_id'])
            assert retry_asset.state=='deleting' and retry_asset.cleanup_after>=now[0]+timedelta(hours=24)
            assert old_key in fake.objects
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert old_key in fake.objects
            now[0]+=timedelta(hours=25)
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert old_key not in fake.objects and (await asset(old['image_id'])).state=='deleted'
            check(await s1.patch(f"/products/{p1['product_id']}",json={'main_image':old['image_url']}),403)
            print('PASS shared inactive references / orphan upload compensation / hold protection / persistent 24h retry / generation delete / deleted association rejection')

            # 遠端刪除成功但 DB 審計失敗，持久 deleting 意圖可在 NotFound 後完成。
            pending=check(await upload())
            pending_asset=await asset(pending['image_id'])
            pending_key=(pending_asset.bucket,pending_asset.object_name)
            now[0]+=timedelta(days=8)
            original_audit=image_service._audit

            async def fail_complete(db,request,actor_id,action,*args,**kwargs):
                if action=='IMAGE_DELETE_COMPLETE':
                    raise RuntimeError('completion audit unavailable')
                await original_audit(db,request,actor_id,action,*args,**kwargs)

            with monkeypatch.context() as patch:
                patch.setattr(image_service,'_audit',fail_complete)
                assert check(await admin.post('/upload/cleanup',json={'dry_run':False}))['failed']>=1
            assert pending_key not in fake.objects and (await asset(pending['image_id'])).state=='deleting'
            now[0]+=timedelta(hours=25)
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert (await asset(pending['image_id'])).state=='deleted'
            # generation 或 GCS 保留狀態不符時，不得刪除遠端物件。
            protected=[check(await upload()) for _ in range(2)]
            protected_assets=[await asset(item['image_id']) for item in protected]
            changed,remote_held=protected_assets
            fake.objects[changed.bucket,changed.object_name]['generation']+=1000
            fake.objects[remote_held.bucket,remote_held.object_name]['held']=True
            now[0]+=timedelta(days=8)
            assert check(await admin.post('/upload/cleanup',json={'dry_run':False}))['failed']>=2
            for protected_asset in protected_assets:
                assert (protected_asset.bucket,protected_asset.object_name) in fake.objects
            # 下架／停用只移除公開輸出，已關聯物件保持正常。
            check(await buyer.post('/cart',json={'product_id':p1['product_id'],'quantity':1}),201)
            check(await s1.delete(f"/products/{p1['product_id']}"),204)
            check(await visitor.get(f"/products/{p1['product_id']}"),403)
            assert p1['product_id'] not in [p['product_id'] for p in check(await visitor.get('/products'))['items']]
            assert check(await buyer.get('/cart'))['items'][0]['product']['main_image'] is None
            new_asset=await asset(new['image_id'])
            new_key=(new_asset.bucket,new_asset.object_name)
            assert new_key in fake.objects
            check(await admin.patch('/users/2/activation',json={'is_active':False}))
            check(await upload(),401)
            check(await admin.post('/upload/cleanup',json={'dry_run':False}))
            assert new_key in fake.objects
            print('PASS GCS-success/DB-failure recovery / downlisting public URL suppression / Seller disable preserves associated objects')
    finally:
        env.app.dependency_overrides.clear()
        env.app.state.limiter.enabled=True
        await fresh.dispose()
        await engine.dispose()
