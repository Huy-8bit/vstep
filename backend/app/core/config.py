from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://vstep:vstep_dev@localhost:5432/vstep"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6"
    jwt_secret: str = "local-development-secret-change-before-production-2026"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    frontend_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def production_secret(self):
        if self.app_env == "production" and (
            len(self.jwt_secret) < 32 or self.jwt_secret.startswith("local-development")
        ):
            raise ValueError("JWT_SECRET must be a unique secret of at least 32 characters.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
