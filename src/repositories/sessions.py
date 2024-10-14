from src.models import Session
from src.repositories.abstract import SQLAlchemyRepository


class SessionsRepository(SQLAlchemyRepository[Session]):
    model = Session
    primary_key = "session_id"
