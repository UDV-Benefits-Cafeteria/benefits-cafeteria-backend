import logging
import sys
from typing import Any, Dict, List, Tuple

from loguru import logger
from pydantic import PostgresDsn, SecretStr

from src.settings.base import BaseAppSettings
from src.settings.logging import InterceptHandler


class AppSettings(BaseAppSettings):
    debug: bool = True
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "UDV Benefits app"
    version: str = "0.0.1"

    database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@db/postgres"
    max_connection_count: int = 10
    min_connection_count: int = 10

    secret_key: SecretStr = "555555444444444111111"

    api_v1_prefix: str = "/api/v1"

    jwt_token_prefix: str = "Token"

    allowed_hosts: List[str] = ["*"]

    logging_level: int = logging.INFO
    loggers: Tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    class ConfigDict:
        validate_assignment = True

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }

    def configure_logging(self) -> None:
        logging.getLogger().handlers = [InterceptHandler()]
        for logger_name in self.loggers:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler(level=self.logging_level)]

        logger.configure(handlers=[{"sink": sys.stderr, "level": self.logging_level}])
