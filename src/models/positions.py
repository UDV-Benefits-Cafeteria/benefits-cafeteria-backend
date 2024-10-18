from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Benefit, User


class Position(Base):
    """
    Represents a job position within the system.

    This class maps to the 'positions' table in the database and includes
    attributes for the position's unique identifier and name.

    Attributes:
        id (int): The unique identifier for the position.
        name (str): The name of the position. Must be unique.
        users (List[User]): A list of users associated with this position.
        benefits (List[Benefit]): A list of benefits associated with this position.
    """

    __tablename__ = "positions"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="position")
    benefits: Mapped[List["Benefit"]] = relationship(
        "Benefit", secondary="benefit_positions", back_populates="positions"
    )
