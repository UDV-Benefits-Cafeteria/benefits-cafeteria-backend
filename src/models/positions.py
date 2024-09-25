from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import User, Benefit


class Position(Base):
    __tablename__ = "positions"

    repr_cols = ("id", "name")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(
        "User", back_populates="position"
    )
    benefits: Mapped[List["Benefit"]] = relationship(
        "Benefit",
        secondary="benefit_positions",
        back_populates="positions"
    )
