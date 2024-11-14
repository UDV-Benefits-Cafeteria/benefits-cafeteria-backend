from src.models.benefits import Category
from src.repositories.base import SQLAlchemyRepository


class CategoriesRepository(SQLAlchemyRepository[Category]):
    model = Category
