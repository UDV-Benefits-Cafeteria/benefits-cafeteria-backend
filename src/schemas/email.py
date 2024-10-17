from typing import Any

from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    email: list[EmailStr]
    body: dict[str, Any]
