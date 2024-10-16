from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    session_id: str
    user_id: int
    expires_at: datetime
    csrf_token: str


class SessionRead(SessionBase):
    model_config = ConfigDict(from_attributes=True)
