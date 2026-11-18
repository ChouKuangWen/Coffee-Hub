from pydantic_settings import BaseSettings  # 自動從環境變數加載及型別驗證
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = "development"
    ENABLE_SIMULATED_CHECKOUT: bool = False
    # 圖片使用獨立、顯式設定的 bucket，不回退到舊 GCP_BUCKET_NAME。
    IMAGE_STORAGE_ENABLED: bool = False
    GCS_IMAGE_BUCKET: str = ""
    IMAGE_MAX_DIMENSION: int = Field(8192, ge=1, le=8192)
    IMAGE_MAX_PIXELS: int = Field(20_000_000, ge=1, le=20_000_000)
    IMAGE_CLEANUP_GRACE_DAYS: int = Field(7, ge=7)
    IMAGE_CLEANUP_RETRY_HOURS: int = Field(24, ge=24)
    IMAGE_DELETE_ENABLED: bool = False
    SECRET_KEY: str                   # 從 .env 讀取驗證金鑰
    ALGORITHM: str                    # 從 .env 讀取演算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # 從 .env 讀取過期時間
    REFRESH_TOKEN_EXPIRE_DAYS: int   # 從 .env 讀取REFRESH_TOKEN有效時間(天)

    class Config:
        env_file = ".env"

settings = Settings()
