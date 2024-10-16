from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    """
    Base model for session-related data.

    Attributes:
        session_id (str): Unique identifier for the session.
        user_id (int): Identifier for the user associated with the session.
        expires_at (datetime): The expiration date and time of the session.
        csrf_token (str): The CSRF token for securing the session.
    """

    session_id: str
    user_id: int
    expires_at: datetime
    csrf_token: str


class SessionRead(SessionBase):
    """
    Model for reading session information.

    Inherits from SessionBase and configures the model to use attributes as field names.
    """

    model_config = ConfigDict(from_attributes=True)
