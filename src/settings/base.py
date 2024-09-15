from enum import Enum

from pydantic_settings import BaseSettings


class AppEnvTypes(Enum):
    prod: str = "prod"
    dev: str = "dev"
    test: str = "test"


class BaseAppSettings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.dev

    class ConfigDict:
        env_file = ".env"
        extra = "allow"
