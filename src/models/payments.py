from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import User


class CoinPayment(Base):
    """
    Represents a payment made using coins within the system.

    This class maps to the 'coin_payments' table in the database and includes
    attributes for the payment's unique identifier, associated user, amount,
    optional comment, and payer information.

    Attributes:
        id (int): The unique identifier for the coin payment.
        user_id (Optional[int]): The identifier of the user making the payment.
        amount (int): The amount of coins involved in the payment.
        comment (Optional[str]): An optional comment associated with the payment.
        payer_id (Optional[int]): The identifier of the user processing the payment.

    Relationships:
        user (User): The user making the payment, linked to the User model.
        payer (User): The user processing the payment, linked to the User model.
    """

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
        "User",
        back_populates="coin_payments",
        foreign_keys=[user_id],
    )
    payer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="processed_payments",
        foreign_keys=[payer_id],
    )
