"""
This file is made for testing.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class BenefitImageBase(BaseModel):
    image_url: str
    is_primary: bool = False
    description: Optional[str] = None


class BenefitImageCreate(BenefitImageBase):
    pass


class BenefitImageUpdate(BenefitImageBase):
    pass


class BenefitImageRead(BenefitImageBase):
    id: int
    benefit_id: int

    class Config:
        from_attributes = True


class BenefitBase(BaseModel):
    name: str
    is_active: bool = True
    description: Optional[str] = None
    cost_id: Optional[int] = None
    real_currency_cost: Optional[Decimal] = None
    amount: Optional[int] = None
    is_fixed_period: bool = False
    usage_limit: Optional[int] = None
    usage_period_days: Optional[int] = None
    period_start_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_by: Optional[datetime] = None


class BenefitCreate(BenefitBase):
    images: Optional[List[BenefitImageCreate]] = None


class BenefitUpdate(BenefitBase):
    name: Optional[str] = None
    images: Optional[List[BenefitImageUpdate]] = None


class BenefitRead(BenefitBase):
    id: int
    images: Optional[List[BenefitImageRead]] = None

    class Config:
        from_attributes = True


class BenefitFilter(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    limit: int = 10
    offset: int = 0
