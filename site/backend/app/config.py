from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Prompts Vault API"
    debug: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/prompts_vault",
        description="Async SQLAlchemy URL",
    )
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    jwt_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand",
        description="HS256 signing key for access tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
