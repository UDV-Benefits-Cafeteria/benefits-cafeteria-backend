import datetime
from enum import Enum
from typing import Annotated, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.benefit import BenefitReadPublic
from src.schemas.user import UserRead


class BenefitStatus(str, Enum):
    PENDING = "pending"  # В ожидании
    PROCESSING = "processing"  # В процессе
    APPROVED = "approved"  # Одобрен
    DECLINED = "declined"  # Отклонен


class BenefitRequestSortFields(str, Enum):
    CREATED_AT = "created_at"


class BenefitRequestBase(BaseModel):
    benefit_id: Optional[int] = None
    user_id: Optional[int] = None
    performer_id: Optional[int] = None
    status: BenefitStatus = BenefitStatus.PENDING
    content: Optional[str] = None
    comment: Optional[str] = None


class BenefitRequestCreate(BaseModel):
    benefit_id: int
    status: BenefitStatus = BenefitStatus.PENDING


class BenefitRequestUpdate(BaseModel):
    status: Optional[BenefitStatus] = None
    content: Optional[str] = None
    comment: Optional[str] = None
    performer_id: Optional[int] = None

    model_config = {"extra": "forbid"}


class BenefitRequestRead(BenefitRequestBase):
    id: int
    created_at: datetime.datetime
    benefit: Optional[BenefitReadPublic] = None
    user: Optional[UserRead] = None
    performer: Optional[UserRead] = None
    benefit_id: Annotated[Optional[int], Field(None, exclude=True)]
    user_id: Annotated[Optional[int], Field(None, exclude=True)]
    performer_id: Annotated[Optional[int], Field(None, exclude=True)]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BenefitRequestReadExcel(BenefitRequestRead):
    id: int

    updated_at: datetime.datetime

    user: Annotated[Optional[UserRead], Field(None, exclude=True)]
    performer: Annotated[Optional[UserRead], Field(None, exclude=True)]
    benefit: Annotated[Optional[BenefitReadPublic], Field(None, exclude=True)]

    user_email: Optional[str] = None
    user_fullname: Optional[str] = None
    performer_email: Optional[str] = None
    performer_fullname: Optional[str] = None
    benefit_name: Optional[str] = None

    @model_validator(mode="after")
    def arrange_benefit_request_for_export(self) -> Self:
        if self.user:
            self.user_email = self.user.email
            self.user_fullname = f"{self.user.lastname} {self.user.firstname} {self.user.middlename or ''}".strip()

        if self.performer:
            self.performer_email = self.performer.email
            self.performer_fullname = f"{self.performer.lastname} {self.performer.firstname} {self.performer.middlename or ''}".strip()

        if self.benefit:
            self.benefit_name = self.benefit.name

        return self

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
