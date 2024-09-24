from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class Cost(Base):
    __tablename__ = "costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coins_cost: Mapped[int] = mapped_column(Integer)
    level_cost: Mapped[int] = mapped_column(Integer)
