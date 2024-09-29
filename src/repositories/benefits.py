from typing import List

from sqlalchemy import asc, desc

import src.schemas.benefit as schemas
from src.models import Benefit
from src.utils.repository import SQLAlchemyRepository


class BenefitsRepository(SQLAlchemyRepository[Benefit]):
    model = Benefit

    async def find_all(self, filters: schemas.BenefitFilter) -> List[Benefit]:
        filter_expressions = []

        if filters.is_active is not None:
            filter_expressions.append(self.model.is_active == filters.is_active)

        if filters.name:
            filter_expressions.append(self.model.name.ilike(f"%{filters.name}%"))

        valid_sort_fields = {
            "name": self.model.name,
            "real_currency_cost": self.model.real_currency_cost,
            "available_from": self.model.available_from,
            "amount": self.model.amount,
        }
        order_by = None
        if filters.sort_by in valid_sort_fields:
            sort_field = valid_sort_fields[filters.sort_by]
            if filters.sort_order.lower() == "desc":
                order_by = desc(sort_field)
            else:
                order_by = asc(sort_field)

        return await super().find_all(
            *filter_expressions,
            order_by=order_by,
            limit=filters.limit,
            offset=filters.offset,
        )
