import re
from datetime import date
from enum import Enum
from typing import Annotated, Optional, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo

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
    legal_entity_id: Optional[int] = None
    role: UserRole
    hired_at: date
    is_active: bool = True
    is_adapted: bool = False
    is_verified: bool = False
    coins: int = 0

    @field_validator("firstname", "middlename", "lastname")
    @classmethod
    def check_only_letters(cls, name: str, info: ValidationInfo) -> str:
        if isinstance(name, str):
            pattern = r"^[A-Za-zА-Яа-яЁё]+([\-'][A-Za-zА-Яа-яЁё]+)*(\s[A-Za-zА-Яа-яЁё]+([\-'][A-Za-zА-Яа-яЁё]+)*)*$"
            if not re.fullmatch(pattern, name):
                raise ValueError(
                    f"{info.field_name} contains characters that do not pass validation"
                )
        return name


class UserRegister(BaseModel):
    id: int
    password: Annotated[str, Field(min_length=8, max_length=255)]
    re_password: Annotated[str, Field(min_length=8, max_length=255)]

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        pw1 = self.password
        pw2 = self.re_password
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords are different")
        return self


class UserLogin(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255)]
    password: Annotated[str, Field(min_length=8, max_length=255)]


class UserVerify(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255)]


class UserTokens(BaseModel):
    secret: SecretStr
    refresh: SecretStr


class UserVerified(BaseModel):
    id: int


class UserError(BaseModel):
    error: str


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

    position_id: Optional[int] = Field(None, exclude=True)
    legal_entity_id: Optional[int] = Field(None, exclude=True)

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
