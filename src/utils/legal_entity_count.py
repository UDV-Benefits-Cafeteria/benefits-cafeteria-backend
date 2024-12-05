from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.models.users import UserRole


async def get_legal_entity_counts(
    legal_entity_id: int, session: AsyncSession
) -> tuple[int, int]:
    """
    Retrieve the number of employees and staff members for a specific legal entity.
    """
    count_statement = select(
        func.count(User.id)
        .filter(User.role == UserRole.EMPLOYEE, User.legal_entity_id == legal_entity_id)
        .label("employee_count"),
        func.count(User.id)
        .filter(
            User.role.in_([UserRole.HR, UserRole.ADMIN]),
            User.legal_entity_id == legal_entity_id,
        )
        .label("staff_count"),
    )

    result = await session.execute(count_statement)
    counts = result.fetchone()

    employee_count = counts.employee_count if counts.employee_count else 0
    staff_count = counts.staff_count if counts.staff_count else 0

    return employee_count, staff_count


async def get_multiple_legal_entity_counts(
    legal_entity_ids: list[int], session: AsyncSession
) -> dict[int, tuple[int, int]]:
    """
    Retrieve employee and staff counts for multiple legal entities.
    Example:
        {
            1: (10, 2),
            2: (5, 1),
            3: (0, 0)
        }
    """
    count_statement = (
        select(
            User.legal_entity_id,
            func.count(User.id)
            .filter(
                User.role == UserRole.EMPLOYEE,
                User.legal_entity_id == User.legal_entity_id,
            )
            .label("employee_count"),
            func.count(User.id)
            .filter(
                User.role.in_([UserRole.HR, UserRole.ADMIN]),
                User.legal_entity_id == User.legal_entity_id,
            )
            .label("staff_count"),
        )
        .where(User.legal_entity_id.in_(legal_entity_ids))
        .group_by(User.legal_entity_id)
    )

    result = await session.execute(count_statement)
    # Example : [(1, 10, 2), (2, 5, 1), (3, 0, 0)] - corresponds to example in docstring
    counts = result.fetchall()

    # Initialize with all zeroes for counts
    counts_dict: dict[int, tuple[int, int]] = {
        legal_entity_id: (0, 0) for legal_entity_id in legal_entity_ids
    }

    for row in counts:
        counts_dict[row.legal_entity_id] = (
            row.employee_count if row.employee_count else 0,
            row.staff_count if row.staff_count else 0,
        )

    return counts_dict
