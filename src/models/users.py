import datetime as dt
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from .applications import Answer, Question
    from .benefits import BenefitProduct
    from .payments import CoinPayment


class UserRole(enum.Enum):
    employee = "employee"
    hr = "hr"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str] = mapped_column(String)
    lastname: Mapped[str] = mapped_column(String)
    middlename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    position: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_adapted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    coins: Mapped[int] = mapped_column(Integer, default=0)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole))
    hired_at: Mapped[DateTime] = mapped_column(DateTime)
    legal_entity_id: Mapped[int] = mapped_column(
        ForeignKey("legal_entities.id", ondelete="CASCADE")
    )

    legal_entity: Mapped["LegalEntity"] = relationship(
        "LegalEntity", back_populates="users"
    )

    coin_payments: Mapped[List["CoinPayment"]] = relationship(
        "CoinPayment", back_populates="user", cascade="all, delete-orphan"
    )
    processed_payments: Mapped[List["CoinPayment"]] = relationship(
        "CoinPayment", back_populates="hr"
    )

    benefit_products: Mapped[List["BenefitProduct"]] = relationship(
        "BenefitProduct", back_populates="user", cascade="all, delete-orphan"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="user", cascade="all, delete-orphan"
    )
    answers_given: Mapped[List["Answer"]] = relationship("Answer", back_populates="hr")

    @property
    def experience(self) -> int:
        today = datetime.now(dt.UTC)
        delta = today - self.hired_at
        return delta.days // 30


class LegalEntity(Base):
    __tablename__ = "legal_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    users: Mapped[List["User"]] = relationship(
        "User", back_populates="legal_entity", cascade="all, delete-orphan"
    )
