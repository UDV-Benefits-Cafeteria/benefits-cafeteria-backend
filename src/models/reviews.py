from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Benefit, User


class Review(Base):
    __tablename__ = "reviews"

    repr_cols = ("id", "benefit_id", "user_id", "text")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[Text] = mapped_column(Text, nullable=False)

    benefit: Mapped[Optional["Benefit"]] = relationship(
        "Benefit",
        back_populates="reviews",
        lazy="selectin",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviews",
        lazy="selectin",
    )
