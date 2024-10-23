from src.models.benefits import Category
from src.repositories.abstract import SQLAlchemyRepository


class CategoriesRepository(SQLAlchemyRepository[Category]):
    model = Category
