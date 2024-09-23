from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column, Mapped

from db.db import Base


class Cost(Base):
    __tablename__ = 'costs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coins_cost: Mapped[int] = mapped_column(Integer)
    level_cost: Mapped[str] = mapped_column(String)

#как будем обрабатывать ситуацию с несколькими стоимостями? допустим сотрудник работает больше 3 лет, ему что-то доступно бесплатно