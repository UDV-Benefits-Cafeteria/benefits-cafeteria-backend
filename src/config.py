from functools import lru_cache
from typing import Dict, Type

from src.settings.app import AppSettings
from src.settings.base import AppEnvTypes, BaseAppSettings
from src.settings.development import DevAppSettings
from src.settings.production import ProdAppSettings
from src.settings.test import TestAppSettings

environments: Dict[AppEnvTypes, Type[AppSettings]] = {
    AppEnvTypes.dev: DevAppSettings,
    AppEnvTypes.prod: ProdAppSettings,
    AppEnvTypes.test: TestAppSettings,
}


@lru_cache
def get_app_settings() -> AppSettings:
    app_env = BaseAppSettings().app_env
    config = environments[app_env]
    return config()
