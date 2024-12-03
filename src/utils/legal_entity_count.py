from sqlalchemy import func

from src.db.db import sync_session_factory
from src.models import User
from src.models.users import UserRole


def get_legal_entity_counts(legal_entity_id: int) -> tuple[int, int]:
    with sync_session_factory() as session:
        employee_number = (
            session.query(func.count())
            .filter(
                User.legal_entity_id == legal_entity_id, User.role == UserRole.EMPLOYEE
            )
            .scalar()
            or 0
        )

        staff_number = (
            session.query(func.count())
            .filter(
                User.legal_entity_id == legal_entity_id,
                User.role.in_([UserRole.HR, UserRole.ADMIN]),
            )
            .scalar()
            or 0
        )

    return employee_number, staff_number
