import json
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "rewind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Telegram Bot
    BOT_TOKEN: str = "8883951489:AAFBRI_EYJbRG6AqLHRkVXu86e97C8B-McA"
    BOT_USERNAME: str = "anonim_rewind_bot"
    WEBHOOK_HOST: str = "http://localhost:8000"
    WEBHOOK_PATH: str = "/telegram/webhook"
    WEBHOOK_SECRET: str = "rewind_secret_token_12345"
    ADMIN_USER_IDS: List[int] = [7728111589]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./rewind.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    LOCAL_STORAGE_DIR: str = "./data/media"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "rewind-media-archive"
    S3_REGION: str = "us-east-1"

    # Security
    ENCRYPTION_KEY: str = "rewind_default_encryption_key_32chars!"

    # Monetization & Retention
    TRIAL_HOURS: int = 72
    PRO_SUBSCRIPTION_STARS: int = 50
    PRO_SUBSCRIPTION_PERIOD_DAYS: int = 30
    MEDIA_RETENTION_DAYS: int = 30

    @field_validator("ADMIN_USER_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("["):
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [int(x.strip()) for x in v_str.split(",") if x.strip().isdigit()]
        return v or []

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
