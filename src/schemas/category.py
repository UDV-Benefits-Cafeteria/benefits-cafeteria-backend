from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255)]

    @field_validator("name")
    @classmethod
    def name_to_lower(cls, name: str) -> str:
        return name.lower()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
