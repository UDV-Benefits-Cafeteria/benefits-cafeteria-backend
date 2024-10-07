from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.benefit import BenefitRead
from src.schemas.user import UserRead


class BenefitStatus(str, Enum):
    PENDING = "pending"  # В ожидании
    APPROVED = "approved"  # Одобрен
    DECLINED = "declined"  # Отклонен


class BenefitRequestBase(BaseModel):
    benefit_id: Optional[int] = None
    user_id: Optional[int] = None
    status: BenefitStatus = BenefitStatus.PENDING
    content: Optional[str] = None
    comment: Optional[str] = None


class BenefitRequestCreate(BenefitRequestBase):
    pass


class BenefitRequestUpdate(BenefitRequestBase):
    status: Optional[BenefitStatus] = None


class BenefitRequestRead(BenefitRequestBase):
    id: int
    benefit: Optional["BenefitRead"] = None
    user: Optional["UserRead"] = None
    benefit_id: Optional[int] = Field(None, exclude=True)
    user_id: Optional[int] = Field(None, exclude=True)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
