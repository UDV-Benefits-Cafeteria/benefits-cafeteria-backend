from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenefitPositionBase(BaseModel):
    benefit_id: int
    position_id: int


class BenefitPositionCreate(BenefitPositionBase):
    pass


class BenefitPositionUpdate(BenefitPositionBase):
    position_id: Optional[int] = None


class BenefitPositionRead(BenefitPositionBase):
    model_config = ConfigDict(from_attributes=True)
