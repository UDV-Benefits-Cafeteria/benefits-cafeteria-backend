import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from src.db.db import Base

if TYPE_CHECKING:
    from src.models import Position, Question, User


class BenefitImage(Base):
    """
    Represents an image associated with a benefit.

    This class maps to the 'benefit_images' table in the database and includes
    attributes for the image URL, its association with a benefit, and whether it
    is the primary image.

    Attributes:
        id (int): The unique identifier for the image.
        benefit_id (int): The ID of the associated benefit.
        image_url (str): The URL of the image.
        is_primary (bool): Indicates if this is the primary image for the benefit.
        description (Optional[str]): A description of the image.
    """

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
    """
    Represents a benefit that users can request.

    This class maps to the 'benefits' table in the database and includes various
    attributes related to the benefit, such as its name, cost, and associated images.

    Attributes:
        id (int): The unique identifier for the benefit.
        category_id (Optional[int]): The ID of the category this benefit belongs to.
        name (str): The name of the benefit.
        is_active (bool): Indicates if the benefit is currently active.
        description (Optional[str]): A description of the benefit.
        coins_cost (int): The cost of the benefit in coins.
        min_level_cost (int): The minimum level required to request the benefit.
        adaptation_required (bool): Indicates if adaptation is needed.
        real_currency_cost (Optional[Decimal]): The cost of the benefit in real currency.
        amount (Optional[int]): The total amount available.
        is_fixed_period (Optional[bool]): Indicates if the benefit is available for a fixed period.
        usage_limit (Optional[int]): The limit on the number of times the benefit can be used.
        usage_period_days (Optional[int]): The number of days the benefit can be used.
        period_start_date (Optional[datetime]): The start date of the benefit availability.
        available_from (Optional[datetime]): The date from which the benefit is available.
        available_by (Optional[datetime]): The date until which the benefit is available.
    """

    __tablename__ = "benefits"

    repr_cols = ("id", "name", "description")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    coins_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    min_level_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    adaptation_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    real_currency_cost: Mapped[Optional[Numeric]] = mapped_column(
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

    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="benefits"
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
    """
    Enum representing the status of a benefit request.

    Attributes:
        PENDING: The request is awaiting approval.
        APPROVED: The request has been approved.
        DECLINED: The request has been declined.
    """

    PENDING = "pending"  # В ожидании
    APPROVED = "approved"  # Одобрен
    DECLINED = "declined"  # Отклонен


class BenefitRequest(Base):
    """
    Represents a request made by a user for a specific benefit.

    This class maps to the 'benefit_requests' table and includes attributes related
    to the user, benefit, and request status.

    Attributes:
        id (int): The unique identifier for the request.
        benefit_id (Optional[int]): The ID of the requested benefit.
        user_id (Optional[int]): The ID of the user making the request.
        status (BenefitStatus): The current status of the benefit request.
        content (Optional[str]): Any additional content related to the request.
        comment (Optional[str]): Comments on the request.
    """

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
    """
    Represents the association between benefits and positions.

    This class maps to the 'benefit_positions' table, creating a many-to-many
    relationship between benefits and positions.

    Attributes:
        benefit_id (int): The ID of the associated benefit.
        position_id (int): The ID of the associated position.
    """

    __tablename__ = "benefit_positions"

    repr_cols = ("benefit_id", "position_id")

    benefit_id: Mapped[int] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )


class Category(Base):
    """
    Represents a category that groups multiple benefits.

    This class maps to the 'categories' table and includes attributes related
    to the category, such as its name and associated benefits.

    Attributes:
        id (int): The unique identifier for the category.
        name (str): The name of the category.
    """

    __tablename__ = "categories"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    benefits: Mapped[List["Benefit"]] = relationship(
        "Benefit", back_populates="category", cascade="all, delete-orphan"
    )
