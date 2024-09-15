import logging

from src.settings.app import AppSettings


class DevAppSettings(AppSettings):
    debug: bool = True

    title: str = "DEV UDV Benefits settings"

    logging_level: int = logging.DEBUG

    class ConfigDict(AppSettings.ConfigDict):
        env_file = ".env"
