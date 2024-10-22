import enum
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.category import CategoryRead
from src.schemas.position import PositionRead


class BenefitSortFields(str, enum.Enum):
    COINS_COST = "coins_cost"
    MIN_LEVEL_COST = "min_level_cost"
    AMOUNT = "amount"
    REAL_CURRENCY_COST = "real_currency_cost"
    CREATED_AT = "created_at"


class SortOrderField(str, enum.Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class BenefitImageBase(BaseModel):
    image_url: str
    benefit_id: int
    is_primary: bool = False
    description: Optional[str] = None


class BenefitImageCreate(BenefitImageBase):
    pass


class BenefitImageUpdate(BenefitImageBase):
    image_url: Optional[str] = None


class BenefitImageRead(BenefitImageBase):
    id: int
    benefit_id: int

    model_config = ConfigDict(from_attributes=True)


class BenefitBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    category_id: Optional[int] = None
    is_active: bool = True
    description: Optional[str] = None
    real_currency_cost: Annotated[
        Optional[Decimal], Field(ge=0, decimal_places=2, max_digits=10)
    ] = None
    amount: Annotated[Optional[int], Field(ge=0)] = None
    is_fixed_period: bool = False
    usage_limit: Annotated[Optional[int], Field(ge=0)] = None
    usage_period_days: Annotated[Optional[int], Field(ge=0)] = None
    period_start_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_by: Optional[datetime] = None
    coins_cost: Annotated[int, Field(ge=0)]
    min_level_cost: Annotated[int, Field(ge=0)]
    adaptation_required: bool = False


class BenefitCreate(BenefitBase):
    pass


class BenefitUpdate(BenefitBase):
    name: Annotated[Optional[str], Field(min_length=2, max_length=100)] = None
    coins_cost: Annotated[Optional[int], Field(ge=0)] = None
    min_level_cost: Annotated[Optional[int], Field(ge=0)] = None
    adaptation_required: Optional[bool] = None
    is_fixed_period: Optional[bool] = None
    is_active: Optional[bool] = None


class BenefitReadShort(BaseModel):
    id: int
    name: str
    coins_cost: int
    min_level_cost: int
    amount: Optional[int]
    primary_image_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BenefitRead(BenefitBase):
    id: int
    images: Optional[list[BenefitImageRead]] = None
    category: Optional[CategoryRead] = None
    positions: Optional[list[PositionRead]] = None
    category_id: Optional[int] = Field(None, exclude=True)

    model_config = ConfigDict(from_attributes=True)
