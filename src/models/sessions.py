from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import User


class Session(Base):
    """
    Represents a user session in the application.

    This class maps to the 'sessions' table in the database and includes
    attributes related to user sessions, including session ID, user ID,
    expiration time, and CSRF token.

    Attributes:
        session_id (str): The unique identifier for the session.
        user_id (int): The identifier of the user associated with this session.
        expires_at (datetime): The expiration date and time of the session.
        csrf_token (str): The CSRF token associated with this session.

    Relationships:
        user (User): The user associated with this session, linked to the User model.
    """

    __tablename__ = "sessions"

    updated_at = None

    session_id: Mapped[str] = mapped_column(
        String(255), primary_key=True, unique=True, nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    csrf_token: Mapped[str] = mapped_column(String(43), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(session_id='{self.session_id}', user_id={self.user_id})>"
