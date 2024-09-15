import logging

from pydantic import PostgresDsn, SecretStr

from src.settings.app import AppSettings


class TestAppSettings(AppSettings):
    debug: bool = True

    title: str = "Test UDV Benefits settings"

    secret_key: SecretStr = SecretStr("test_secret")

    database_url: PostgresDsn
    max_connection_count: int = 5
    min_connection_count: int = 5

    logging_level: int = logging.DEBUG
