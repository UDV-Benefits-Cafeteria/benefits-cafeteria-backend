from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class Cost(Base):
    __tablename__ = "costs"

    repr_cols = ("id", "coins_cost", "min_level_cost")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coins_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    min_level_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    adaptation_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
