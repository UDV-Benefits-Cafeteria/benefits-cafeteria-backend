from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.db import Base

if TYPE_CHECKING:
    from src.models import User


class LegalEntity(Base):
    """
    Represents a legal entity within the system.

    This class maps to the 'legal_entities' table in the database and includes
    attributes for the entity's unique identifier and name.

    Attributes:
        id (int): The unique identifier for the legal entity.
        name (str): The name of the legal entity. Must be unique.
        users (List[User]): A list of users associated with this legal entity.
    """

    __tablename__ = "legal_entities"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="legal_entity")
