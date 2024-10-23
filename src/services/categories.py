import src.schemas.category as schemas
from src.repositories.categories import CategoriesRepository
from src.services.base import BaseService


class CategoriesService(
    BaseService[schemas.CategoryCreate, schemas.CategoryRead, schemas.CategoryUpdate]
):
    repo = CategoriesRepository()
    create_schema = schemas.CategoryCreate
    read_schema = schemas.CategoryRead
    update_schema = schemas.CategoryUpdate
