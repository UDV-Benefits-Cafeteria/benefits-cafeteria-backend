from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BenefitImageBase(BaseModel):
    image_url: str
    is_primary: bool = False
    description: Optional[str] = None


class BenefitImageCreate(BenefitImageBase):
    pass


class BenefitImageUpdate(BaseModel):
    image_url: Optional[str] = None


class BenefitImageRead(BenefitImageBase):
    id: int
    benefit_id: int

    model_config = ConfigDict(from_attributes=True)


class BenefitBase(BaseModel):
    name: Annotated[str, Field(max_length=100)]
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
    images: Optional[List[BenefitImageCreate]] = None


class BenefitUpdate(BenefitBase):
    name: Annotated[Optional[str], Field(max_length=100)] = None
    coins_cost: Annotated[Optional[int], Field(ge=0)]
    min_level_cost: Annotated[Optional[int], Field(ge=0)]
    images: Optional[List[BenefitImageCreate]] = None


class BenefitRead(BenefitBase):
    id: int
    images: Optional[List[BenefitImageRead]] = None

    model_config = ConfigDict(from_attributes=True)
