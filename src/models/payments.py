from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from db.db import Base

if TYPE_CHECKING:
    from models import User


class CoinPayment(Base):
    __tablename__ = 'coinpayments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hr_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))

    user: Mapped['User'] = relationship('User', back_populates='coin_payments', foreign_keys=[user_id])
    hr: Mapped[Optional['User']] = relationship('User', back_populates='processed_payments', foreign_keys=[hr_id])



