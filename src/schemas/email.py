from typing import Any, Dict, List

from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: Dict[str, Any]
