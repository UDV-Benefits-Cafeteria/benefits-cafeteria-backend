import datetime as dt
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.custom_types import FileType

if TYPE_CHECKING:
    from src.models import BenefitRequest, LegalEntity, Position, Review, Session


class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"


class User(Base):
    """
    Represents a user in the application.

    This class maps to the 'users' table in the database and contains
    attributes related to user information, roles, and relationships with
    other entities in the application.

    Attributes:
        id (int): The unique identifier for the user.
        email (str): The user's email address, which must be unique.
        firstname (str): The user's first name.
        lastname (str): The user's last name.
        middlename (Optional[str]): The user's middle name (if applicable).
        position_id (Optional[int]): The ID of the user's position, linked to the Position model.
        role (UserRole): The role of the user, defined as an enumeration.
        password (str): The user's password (hashed).
        hired_at (date): The date the user was hired.
        is_active (bool): Indicates if the user account is active.
        is_adapted (bool): Indicates if the user has completed adaptation.
        is_verified (bool): Indicates if the user has verified their account.
        coins (int): The number of coins the user has.
        legal_entity_id (Optional[int]): The ID of the legal entity the user belongs to.
    """

    __tablename__ = "users"

    repr_cols = ("id", "email", "firstname", "lastname")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    middlename: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(
            UserRole,
            native_enum=False,
            name="user_role_enum",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    hired_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_adapted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    legal_entity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("legal_entities.id", ondelete="SET NULL"), nullable=True
    )
    image_url: Mapped[FileType] = mapped_column(FileType(), nullable=True)

    legal_entity: Mapped[Optional["LegalEntity"]] = relationship(
        "LegalEntity",
        back_populates="users",
        lazy="selectin",
    )
    position: Mapped[Optional["Position"]] = relationship(
        "Position",
        back_populates="users",
        lazy="selectin",
    )
    benefit_requests: Mapped[List["BenefitRequest"]] = relationship(
        "BenefitRequest",
        back_populates="user",
        foreign_keys="BenefitRequest.user_id",
    )
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")

    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def experience(self) -> int:
        """
        Calculates the user's experience in days based on the hired date.

        :return: days
        :rtype: int
        """
        today = dt.date.today()
        delta = today - self.hired_at
        return delta.days

    @property
    def level(self) -> int:
        """
        Calculates the user's level based on experience.

        The level is determined by dividing the number of experience days by 30.

        :return: level
        :rtype: int
        """
        experience_days = self.experience
        return experience_days // 30
