from typing import Any

from fastapi_storages.integrations.sqlalchemy import FileType as _FileType

from src.utils.s3 import storage


class FileType(_FileType):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(storage=storage, *args, **kwargs)
