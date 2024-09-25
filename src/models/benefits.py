import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import Cost, Position, Question, User


class Benefit(Base):
    __tablename__ = "benefits"

    repr_cols = ("id", "name", "description")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    cost_id: Mapped[int] = mapped_column(ForeignKey("costs.id"), nullable=False)
    real_currency_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uses_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uses_max_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uses_update_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    available_from: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    available_by: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    cost: Mapped["Cost"] = relationship("Cost")
    images: Mapped[List["BenefitImage"]] = relationship(
        "BenefitImage", back_populates="benefit"
    )
    categories: Mapped[List["BenefitCategory"]] = relationship(
        "BenefitCategory", back_populates="benefit"
    )
    requests: Mapped[List["BenefitRequest"]] = relationship(
        "BenefitRequest", back_populates="benefit", cascade="all, delete-orphan"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="benefit"
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position", secondary="benefit_positions", back_populates="benefits"
    )


class BenefitStatus(enum.Enum):
    PENDING = "pending"  # В ожидании
    APPROVED = "approved"  # Одобрен
    PROCESSED = "processed"  # Обработан
    DECLINED = "declined"  # Отклонен
    COMPLETED = "completed"  # Завершен


class BenefitRequest(Base):
    __tablename__ = "benefit_requests"

    repr_cols = ("id", "benefit_id", "user_id", "status")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped["BenefitStatus"] = mapped_column(
        SQLAlchemyEnum(BenefitStatus),
        default=BenefitStatus.PENDING,
        index=True,
        nullable=False,
    )
    content: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    benefit: Mapped["Benefit"] = relationship("Benefit", back_populates="requests")
    user: Mapped["User"] = relationship("User", back_populates="benefit_requests")


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
    category: Mapped["Category"] = relationship("Category")


class Category(Base):
    __tablename__ = "categories"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
