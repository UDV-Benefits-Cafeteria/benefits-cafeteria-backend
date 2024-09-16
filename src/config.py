from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_TITLE: str = "UDV Benefits Cafeteria API"
    APP_DESCRIPTION: str = "Api for UDV Benefits Cafeteria"
    APP_VERSION: str = "0.1.0"

    DEBUG: str

    DB_HOST: str
    POSTGRES_USER: str
    POSTGRES_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASS}@{self.DB_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"  # noqa

    model_config = SettingsConfigDict(env_file=Path(__file__).parents[1] / ".env")


settings = Settings()
