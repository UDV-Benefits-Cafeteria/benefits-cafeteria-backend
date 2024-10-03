import datetime as dt
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.db import Base

if TYPE_CHECKING:
    from models import (
        Answer,
        BenefitRequest,
        CoinPayment,
        LegalEntity,
        Position,
        Question,
    )


class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    repr_cols = ("id", "email", "firstname", "lastname")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    firstname: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), nullable=False)
    middlename: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    position_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, native_enum=False, name="user_role_enum"),
        nullable=False,
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    hired_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_adapted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    legal_entity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True
    )

    legal_entity: Mapped[Optional["LegalEntity"]] = relationship(
        "LegalEntity", back_populates="users"
    )
    position: Mapped[Optional["Position"]] = relationship(
        "Position", back_populates="users"
    )
    coin_payments: Mapped[List["CoinPayment"]] = relationship(
        "CoinPayment",
        back_populates="user",
        foreign_keys="CoinPayment.user_id",
    )
    processed_payments: Mapped[List["CoinPayment"]] = relationship(
        "CoinPayment",
        back_populates="payer",
        foreign_keys="CoinPayment.payer_id",
    )
    benefit_requests: Mapped[List["BenefitRequest"]] = relationship(
        "BenefitRequest", back_populates="user"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="user"
    )
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="user")

    @property
    def experience(self) -> int:
        today = dt.date.today()
        delta = today - self.hired_at
        return delta.days

    @property
    def level(self) -> int:
        experience_days = self.experience
        return experience_days // 30
