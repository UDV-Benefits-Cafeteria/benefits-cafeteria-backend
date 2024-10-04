import enum
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from src.db.db import Base

if TYPE_CHECKING:
    from src.models import Position, Question, User


class BenefitImage(Base):
    __tablename__ = "benefit_images"

    repr_cols = ("id", "benefit_id", "description")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)

    benefit: Mapped["Benefit"] = relationship("Benefit", back_populates="images")


class Benefit(Base):
    __tablename__ = "benefits"

    repr_cols = ("id", "name", "description")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    coins_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    min_level_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    adaptation_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    real_currency_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_fixed_period: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=False
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    period_start_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    available_from: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    available_by: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    images: Mapped[List["BenefitImage"]] = relationship(
        "BenefitImage",
        back_populates="benefit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    image_primary: Mapped[Optional["BenefitImage"]] = relationship(
        "BenefitImage",
        primaryjoin=and_(
            id == foreign(BenefitImage.benefit_id), BenefitImage.is_primary.is_(True)
        ),
        uselist=False,
        viewonly=True,
        lazy="selectin",
    )

    images_secondary: Mapped[List["BenefitImage"]] = relationship(
        "BenefitImage",
        primaryjoin=and_(
            id == foreign(BenefitImage.benefit_id), BenefitImage.is_primary.is_(False)
        ),
        viewonly=True,
        lazy="selectin",
    )
    categories: Mapped[List["BenefitCategory"]] = relationship(
        "BenefitCategory", back_populates="benefit", cascade="all, delete-orphan"
    )
    requests: Mapped[List["BenefitRequest"]] = relationship(
        "BenefitRequest", back_populates="benefit"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="benefit", cascade="all, delete-orphan"
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position", secondary="benefit_positions", back_populates="benefits"
    )


class BenefitStatus(enum.Enum):
    PENDING = "pending"  # В ожидании
    APPROVED = "approved"  # Одобрен
    DECLINED = "declined"  # Отклонен


class BenefitRequest(Base):
    __tablename__ = "benefit_requests"

    repr_cols = ("id", "benefit_id", "user_id", "status")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("benefits.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped["BenefitStatus"] = mapped_column(
        SQLAlchemyEnum(BenefitStatus, native_enum=False, name="benefit_status_enum"),
        default=BenefitStatus.PENDING,
        index=True,
        nullable=False,
    )
    content: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    benefit: Mapped[Optional["Benefit"]] = relationship(
        "Benefit", back_populates="requests"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="benefit_requests"
    )


class BenefitPosition(Base):
    __tablename__ = "benefit_positions"

    repr_cols = ("benefit_id", "position_id")

    benefit_id: Mapped[int] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )


class BenefitCategory(Base):
    __tablename__ = "benefit_categories"

    repr_cols = ("id", "benefit_id", "category_id")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    benefit: Mapped["Benefit"] = relationship("Benefit", back_populates="categories")
    category: Mapped["Category"] = relationship(
        "Category", back_populates="benefit_categories"
    )


class Category(Base):
    __tablename__ = "categories"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    benefit_categories: Mapped[List["BenefitCategory"]] = relationship(
        "BenefitCategory", back_populates="category", cascade="all, delete-orphan"
    )
