from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import User


class CoinPayment(Base):
    __tablename__ = "coin_payments"

    repr_cols = ("id", "user_id", "amount")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="coin_payments", foreign_keys=[user_id]
    )
    payer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="processed_payments", foreign_keys=[payer_id]
    )
