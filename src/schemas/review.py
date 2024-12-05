import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.benefit import BenefitReadPublic
from src.schemas.user import UserRead


class ReviewBase(BaseModel):
    text: str
    benefit_id: Optional[int] = None
    user_id: Optional[int] = None


class ReviewCreate(BaseModel):
    text: str
    benefit_id: int


class ReviewUpdate(BaseModel):
    text: str


class ReviewRead(ReviewBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    benefit: Optional[BenefitReadPublic] = None
    user: Optional[UserRead] = None
    benefit_id: Annotated[Optional[int], Field(None, exclude=True)]
    user_id: Annotated[Optional[int], Field(None, exclude=True)]

    model_config = ConfigDict(from_attributes=True)
