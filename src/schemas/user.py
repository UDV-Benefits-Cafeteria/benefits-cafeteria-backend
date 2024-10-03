from datetime import date
from enum import Enum
from typing import Annotated, Optional, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    model_validator,
)

from src.schemas.legalentity import LegalEntityRead
from src.schemas.position import PositionRead


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255)]
    firstname: Annotated[str, Field(max_length=100)]
    lastname: Annotated[str, Field(max_length=100)]
    middlename: Annotated[Optional[str], Field(max_length=100)] = None
    position_id: Optional[int] = None
    role: UserRole
    hired_at: date
    is_active: bool = True
    is_adapted: bool = False
    is_verified: bool = False
    coins: int = 0
    legal_entity_id: Optional[int] = None


class UserRegister(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=255)]
    re_password: Annotated[str, Field(min_length=8, max_length=255)]

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        pw1 = self.password
        pw2 = self.re_password
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Пароли различаются")
        return self


class UserUpdate(UserBase):
    email: Annotated[Optional[EmailStr], Field(max_length=255)] = None
    firstname: Annotated[Optional[str], Field(max_length=100)] = None
    lastname: Annotated[Optional[str], Field(max_length=100)] = None
    role: Optional[UserRole] = None
    hired_at: Optional[date] = None
    coins: Optional[int] = None


class UserRead(UserBase):
    id: int
    position: Optional["PositionRead"] = None
    legal_entity: Optional["LegalEntityRead"] = None

    @computed_field
    @property
    def experience(self) -> int:
        today = date.today()
        delta = today - self.hired_at
        return delta.days

    @computed_field
    @property
    def level(self) -> int:
        return self.experience // 30

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
