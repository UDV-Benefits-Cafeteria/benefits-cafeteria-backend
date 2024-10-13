from pathlib import Path
from typing import List

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_TITLE: str = "UDV Benefits Cafeteria API"
    APP_DESCRIPTION: str = "Api for UDV Benefits Cafeteria"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = False

    POSTGRES_HOST: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    SECRET_KEY: SecretStr = (
        "unsecured2*t@t3b#6g$^w@zsdz57^x-g^o05@e5aztfn=)r#ijaly1-cy0"
    )

    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_EXPIRE_TIME: int = 86400 * 7  # неделя

    ALLOW_ORIGINS: List[str] = ["*"]

    API_PREFIX: str = "/api"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"  # noqa

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parents[1] / ".env", extra="ignore"
    )


settings = Settings()
