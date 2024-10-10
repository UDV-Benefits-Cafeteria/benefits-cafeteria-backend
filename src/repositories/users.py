from src.models.users import User
from src.repositories.abstract import SQLAlchemyRepository


class UsersRepository(SQLAlchemyRepository[User]):
    model = User
