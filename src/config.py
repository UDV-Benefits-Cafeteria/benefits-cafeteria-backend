import logging
from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_TITLE: str = "UDV Benefits Cafeteria"
    APP_DESCRIPTION: str = "API for UDV Benefits Cafeteria"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = False

    POSTGRES_HOST: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    ELASTIC_PASSWORD: str = "elasticpass"
    ELASTIC_HOST: str = "elasticsearch"
    ELASTIC_PORT: int = 9200

    SECRET_KEY: SecretStr = (
        "unsecured2*t@t3b#6g$^w@zsdz57^x-g^o05@e5aztfn=)r#ijaly1-cy0"
    )

    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_EXPIRE_TIME: int = 86400 * 7  # 7 дней
    SESSION_REFRESH_THRESHOLD: int = 86400 * 1  # 1 день

    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_EXPIRE_TIME: int = 86400 * 7  # 7 дней

    SENTRY_DSN: str = "emptyurl"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_SAMPLE_PROFILER_RATE: float = 1.0
    SENTRY_ENVIRONMENT: str = "development"

    DOMAIN: str = "example.site"

    MAIL_USERNAME: str = "username"
    MAIL_PASSWORD: str = "passwd"
    MAIL_FROM: EmailStr = "test@email.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "mailserver"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = False

    ALLOW_ORIGINS: list[str] = ["*"]
    ALLOW_HOSTS: list[str] = ["*"]

    API_PREFIX: str = "/api"

    AWS_ACCESS_KEY_ID: str = "access"
    AWS_SECRET_ACCESS_KEY: str = "secret"
    AWS_S3_BUCKET_NAME: str = "test"
    AWS_S3_ENDPOINT_URL: str = "s3.amazonaws.com"
    AWS_DEFAULT_ACL: str = "public-read"
    AWS_S3_USE_SSL: bool = True

    REDIS_PASSWORD: str = "someverysecuredpass"
    REDIS_USER: str = "user"
    REDIS_USER_PASSWORD: str = "pass"
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = 6379

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"  # noqa

    @property
    def ELASTIC_URL(self) -> str:
        return f"http://{self.ELASTIC_HOST}:{self.ELASTIC_PORT}"

    @property
    def REDIS_BASE_URL(self) -> RedisDsn:
        return f"redis://{self.REDIS_USER}:{self.REDIS_USER_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def REDIS_LIMITER_URL(self) -> RedisDsn:
        return self.REDIS_BASE_URL + "/0"

    # for future
    @property
    def REDIS_CACHE_URL(self) -> RedisDsn:
        return self.REDIS_BASE_URL + "/1"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parents[1] / ".env", extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()
