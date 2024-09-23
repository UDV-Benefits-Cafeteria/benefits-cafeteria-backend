from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import User


class CoinPayment(Base):
    __tablename__ = "coinpayments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hr_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    user: Mapped["User"] = relationship(
        "User", back_populates="coin_payments", foreign_keys=[user_id]
    )
    hr: Mapped[Optional["User"]] = relationship(
        "User", back_populates="processed_payments", foreign_keys=[hr_id]
    )
