from src.repositories.abstract import SQLAlchemyRepository
from src.models.users import User


class UsersRepository(SQLAlchemyRepository[User]):
    model = User
