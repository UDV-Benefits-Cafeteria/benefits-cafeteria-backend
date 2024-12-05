import datetime
import re
from datetime import date
from enum import Enum
from typing import Annotated, Optional, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo

from src.schemas.legalentity import LegalEntityRead
from src.schemas.position import PositionRead


class UserSortFields(str, Enum):
    HIRED_AT = "hired_at"
    FULLNAME = "fullname"
    COINS = "coins"


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255)]
    firstname: Annotated[str, Field(max_length=100)]
    lastname: Annotated[str, Field(max_length=100)]
    middlename: Annotated[Optional[str], Field(max_length=100)] = None
    coins: Annotated[Optional[int], Field(ge=0)] = None
    position_id: Optional[int] = None
    legal_entity_id: Optional[int] = None
    role: UserRole
    hired_at: date = Field(...)
    is_active: bool = True
    is_verified: bool = False
    is_adapted: bool = False

    @field_validator("firstname", "middlename", "lastname")
    @classmethod
    def check_only_letters(
        cls, name: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Validate that names contain only letters and specific characters."""
        if name is None:
            return None
        if isinstance(name, str):
            pattern = r"^[A-Za-zА-Яа-яЁё]+([\-'][A-Za-zА-Яа-яЁё]+)*(\s[A-Za-zА-Яа-яЁё]+([\-'][A-Za-zА-Яа-яЁё]+)*)*$"
            if not re.fullmatch(pattern, name):
                raise ValueError(
                    f"{info.field_name} contains characters that do not pass validation"
                )
        return name

    @field_validator("hired_at")
    @classmethod
    def check_hired_at(cls, value: date):
        if value > date.today():
            raise ValueError("Hire date cannot be in the future.")
        return value


class UserRegister(BaseModel):
    id: int
    password: Annotated[str, Field(min_length=8, max_length=255)]
    re_password: Annotated[str, Field(min_length=8, max_length=255)]

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        """Ensure that the password and re-entered password match."""
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


class UserVerified(BaseModel):
    id: int


class UserCreate(UserBase):
    is_verified: Annotated[bool, Field(default=False, exclude=True)]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserCreateExcel(UserBase):
    position_name: Optional[str] = None
    legal_entity_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserUpdate(UserBase):
    email: Annotated[Optional[EmailStr], Field(max_length=255)] = None
    firstname: Annotated[Optional[str], Field(max_length=100)] = None
    lastname: Annotated[Optional[str], Field(max_length=100)] = None
    role: Optional[UserRole] = None
    hired_at: Annotated[Optional[date], Field(..., le=date.today())] = None
    is_active: Optional[bool] = None
    is_adapted: Optional[bool] = None


class UserRead(UserBase):
    id: int
    position: Optional[PositionRead] = None
    legal_entity: Optional[LegalEntityRead] = None
    image_url: Optional[str] = None
    position_id: Annotated[Optional[int], Field(None, exclude=True)]
    legal_entity_id: Annotated[Optional[int], Field(None, exclude=True)]

    @computed_field
    @property
    def experience(self) -> int:
        """Calculate the user's experience in days based on the hired date."""
        today = date.today()
        delta = today - self.hired_at
        return delta.days

    @computed_field
    @property
    def level(self) -> int:
        """Calculate the user's level based on their experience."""
        return self.experience // 30

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserReadExcel(UserRead):
    legal_entity: Annotated[Optional[LegalEntityRead], Field(None, exclude=True)]
    position: Annotated[Optional[PositionRead], Field(None, exclude=True)]
    image_url: Annotated[Optional[str], Field(None, exclude=True)]

    created_at: datetime.datetime
    updated_at: datetime.datetime

    @computed_field
    @property
    def legal_entity_name(self) -> Optional[str]:
        return self.legal_entity.name if self.legal_entity is not None else None

    @computed_field
    @property
    def position_name(self) -> Optional[str]:
        return self.position.name if self.position is not None else None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserUploadError(BaseModel):
    row: int
    error: str


class UserUploadResponse(BaseModel):
    created_users: list[UserRead]
    errors: list[UserUploadError]


class UserValidationResponse(BaseModel):
    valid_users: list[UserCreate]
    errors: list[UserUploadError]


class UserAuth(BaseModel):
    id: int
    is_verified: bool
    password: Annotated[Optional[str], Field(min_length=8, max_length=255)] = None
    model_config = ConfigDict(from_attributes=True)


class UserResetForgetPassword(BaseModel):
    secret_token: str
    new_password: Annotated[str, Field(min_length=8, max_length=255)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=255)]
