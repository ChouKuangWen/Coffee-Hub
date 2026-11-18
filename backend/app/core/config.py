from pydantic_settings import BaseSettings  # 自動從環境變數加載及型別驗證

class Settings(BaseSettings):
    APP_ENV: str = "development"
    ENABLE_SIMULATED_CHECKOUT: bool = False
    SECRET_KEY: str                   # 從 .env 讀取驗證金鑰
    ALGORITHM: str                    # 從 .env 讀取演算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # 從 .env 讀取過期時間
    REFRESH_TOKEN_EXPIRE_DAYS: int   # 從 .env 讀取REFRESH_TOKEN有效時間(天)

    class Config:
        env_file = ".env"

settings = Settings()
