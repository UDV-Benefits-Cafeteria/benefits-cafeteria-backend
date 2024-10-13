from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    session_id: str
    user_id: int
    expires_at: datetime


class SessionCreate(SessionBase):
    user_id: int
    expires_at: datetime
    session_id: Optional[str] = None


class SessionRead(SessionBase):
    model_config = ConfigDict(from_attributes=True)
