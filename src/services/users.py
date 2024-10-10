import src.schemas.user as schemas
from src.services.abstract import AbstractService


class UserService(AbstractService[schemas.UserCreate, schemas.UserRead, schemas.UserUpdate]):
    pass