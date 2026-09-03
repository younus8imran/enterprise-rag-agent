from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Enterprise Intelligence Agent"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # LLM
    ANTHROPIC_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// driver")
        return v

settings = Settings()
