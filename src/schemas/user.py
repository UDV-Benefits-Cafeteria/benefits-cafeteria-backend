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
    """Enumeration for user roles within the application.

    Attributes:
        EMPLOYEE: Base user.
        HR: The HR.
        ADMIN: The admin.
    """

    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"


class UserBase(BaseModel):
    """
    Base model for user-related data.

    This class contains common attributes shared by user models.

    Attributes:
        email (EmailStr): The user's email address, which must be unique.
        firstname (str): The user's first name.
        lastname (str): The user's last name.
        middlename (Optional[str]): The user's middle name (if applicable).
        coins (Optional[int]): The number of coins the user has (non-negative).
        position_id (Optional[int]): The ID of the user's position.
        legal_entity_id (Optional[int]): The ID of the user's legal entity.
        role (UserRole): The role of the user.
        hired_at (date): The date the user was hired.
        is_active (bool): Indicates if the user account is active.
        is_verified (bool): Indicates if the user has verified their account.
        is_adapted (bool): Indicates if the user has completed adaptation.
    """

    email: Annotated[EmailStr, Field(max_length=255)]
    firstname: Annotated[str, Field(max_length=100)]
    lastname: Annotated[str, Field(max_length=100)]
    middlename: Annotated[Optional[str], Field(max_length=100)] = None
    coins: Annotated[Optional[int], Field(ge=0)] = None
    position_id: Optional[int] = None
    legal_entity_id: Optional[int] = None
    role: UserRole
    hired_at: date
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


class UserRegister(BaseModel):
    """
    Model for user registration data.

    Attributes:
        id (int): The unique identifier for the user.
        password (str): The user's password, must be between 8 and 255 characters.
        re_password (str): A second entry for the password to confirm it matches.
    """

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
    """
    Model for user login data.

    Attributes:
        email (EmailStr): The user's email address.
        password (str): The user's password.
    """

    email: Annotated[EmailStr, Field(max_length=255)]
    password: Annotated[str, Field(min_length=8, max_length=255)]


class UserVerify(BaseModel):
    """Model for user verification request."""

    email: Annotated[EmailStr, Field(max_length=255)]


class UserVerified(BaseModel):
    """Model to indicate a verified user."""

    id: int


class UserCreate(UserBase):
    """
    Model for creating a new user.

    Inherits from UserBase, with default values for verification and activation.
    """

    is_verified: bool = Field(default=False, exclude=True)
    is_active: bool = Field(default=True, exclude=True)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserCreateExcel(UserBase):
    position_name: Optional[str] = None
    legal_entity_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UsersCreate(BaseModel):
    """Model for creating multiple users."""

    users: list[UserCreate]


class UserUpdate(UserBase):
    """
    Model for updating user information.

    Attributes:
        email (Optional[EmailStr]): The updated email address.
        firstname (Optional[str]): The updated first name.
        lastname (Optional[str]): The updated last name.
        role (Optional[UserRole]): The updated role of the user.
        hired_at (Optional[date]): The updated hiring date.
        is_active (Optional[bool]): The updated active status.
        is_adapted (Optional[bool]): The updated adapted status.
    """

    email: Annotated[Optional[EmailStr], Field(max_length=255)] = None
    firstname: Annotated[Optional[str], Field(max_length=100)] = None
    lastname: Annotated[Optional[str], Field(max_length=100)] = None
    role: Optional[UserRole] = None
    hired_at: Optional[date] = None
    is_active: Optional[bool] = None
    is_adapted: Optional[bool] = None


class UserRead(UserBase):
    """
    Model for reading user information.

    This includes computed properties for experience and level.

    Attributes:
        id (int): The unique identifier for the user.
        position (Optional[PositionRead]): The user's position information.
        legal_entity (Optional[LegalEntityRead]): The user's legal entity information.
    """

    id: int
    position: Optional["PositionRead"] = None
    legal_entity: Optional["LegalEntityRead"] = None

    position_id: Optional[int] = Field(None, exclude=True)
    legal_entity_id: Optional[int] = Field(None, exclude=True)

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


class UserUploadError(BaseModel):
    """
    Model to indicate an error during user upload.

    Attributes:
        row (int): The row number where the error occurred.
        error (str): A description of the error.
    """

    row: int
    error: str


class UserUploadResponse(BaseModel):
    """Model for the response after uploading users."""

    created_users: list[UserRead]
    errors: list[UserUploadError]


class UserValidationResponse(BaseModel):
    """Model for the response after validating users."""

    valid_users: list[UserCreate]
    errors: list[UserUploadError]


class UserAuth(BaseModel):
    """Model for user authentication data."""

    id: int
    is_verified: bool
    password: Annotated[Optional[str], Field(min_length=8, max_length=255)] = None
    model_config = ConfigDict(from_attributes=True)


class UserResetForgetPassword(BaseModel):
    secret_token: str
    new_password: Annotated[str, Field(min_length=8, max_length=255)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=255)]
