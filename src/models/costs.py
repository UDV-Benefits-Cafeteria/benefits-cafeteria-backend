from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import Benefit


class Cost(Base):
    __tablename__ = "costs"

    repr_cols = ("id", "coins_cost", "min_level_cost")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coins_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    min_level_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    adaptation_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    benefits: Mapped[List["Benefit"]] = relationship("Benefit", back_populates="cost")
