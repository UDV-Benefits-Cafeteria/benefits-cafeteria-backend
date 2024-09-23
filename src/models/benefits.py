import enum
from sqlalchemy import Enum as SQLAlchemyEnum
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, mapped_column, Mapped

from db.db import Base

if TYPE_CHECKING:
    from models import Cost, Question, User


class Benefit(Base):
    __tablename__ = 'benefits'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    cost_id: Mapped[int] = mapped_column(ForeignKey('costs.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    uses_max: Mapped[int] = mapped_column(Integer, nullable=True)
    uses_per_user: Mapped[int] = mapped_column(Integer, nullable=True)
    available_from: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    available_by: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    #можно добавить поле стоимости в реальной валюте, скрытное для пользователя, им будет пользоваться hr

    cost: Mapped['Cost'] = relationship('Cost')
    images: Mapped[List['BenefitImage']] = relationship('BenefitImage', back_populates='benefit')
    categories: Mapped[List['BenefitCategory']] = relationship('BenefitCategory', back_populates='benefit')
    products: Mapped[List['BenefitProduct']] = relationship('BenefitProduct', back_populates='benefit')
    questions: Mapped[List['Question']] = relationship('Question', back_populates='benefit')

class BenefitStatus(enum.Enum):
    pending = "pending"           # В ожидании
    approved = "approved"         # Одобрен
    processed = "processed"       # Обработан
    declined = "declined"         # Отклонен
    completed = "completed"       # Завершен
class BenefitProduct(Base):
    __tablename__ = 'benefitproducts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(ForeignKey('benefits.id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

    content: Mapped[Text] = mapped_column(Text, nullable=True) # что тут должно храниться?

    status: Mapped[BenefitStatus] = mapped_column(SQLAlchemyEnum(BenefitStatus), default=BenefitStatus.pending, index=True)

    benefit: Mapped['Benefit'] = relationship('Benefit', back_populates='products')
    user: Mapped['User'] = relationship('User', back_populates='benefit_products')


class BenefitImage(Base):
    __tablename__ = 'benefitimages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(ForeignKey('benefits.id', ondelete='CASCADE'))
    image_url: Mapped[str] = mapped_column(String)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    benefit: Mapped['Benefit'] = relationship('Benefit', back_populates='images')


class BenefitCategory(Base):
    __tablename__ = 'benefitscategories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(ForeignKey('benefits.id', ondelete='CASCADE'))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'))

    benefit: Mapped['Benefit'] = relationship('Benefit', back_populates='categories')
    category: Mapped['Category'] = relationship('Category')


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
