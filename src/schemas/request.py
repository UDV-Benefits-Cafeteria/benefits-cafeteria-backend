import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.benefit import BenefitRead
from src.schemas.user import UserRead


class BenefitStatus(str, Enum):
    # Old. To support old records
    PENDING = "pending"  # В ожидании
    APPROVED = "approved"  # Одобрен
    DECLINED = "declined"  # Отклонен

    NEW = "new"
    PROCESSING = "processing"
    COMPLETE = "complete"
    CANCELED = "canceled"


class BenefitRequestSortFields(str, Enum):
    CREATED_AT = "created_at"


class BenefitRequestBase(BaseModel):
    benefit_id: Optional[int] = None
    user_id: Optional[int] = None
    status: BenefitStatus = BenefitStatus.NEW
    content: Optional[str] = None
    comment: Optional[str] = None


class BenefitRequestCreate(BenefitRequestBase):
    benefit_id: int
    user_id: int


class BenefitRequestUpdate(BaseModel):
    status: Optional[BenefitStatus] = None
    content: Optional[str] = None
    comment: Optional[str] = None

    model_config = {"extra": "forbid"}


class BenefitRequestRead(BenefitRequestBase):
    id: int
    created_at: datetime.datetime
    benefit: Optional["BenefitRead"] = None
    user: Optional["UserRead"] = None
    benefit_id: Optional[int] = Field(None, exclude=True)
    user_id: Optional[int] = Field(None, exclude=True)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
