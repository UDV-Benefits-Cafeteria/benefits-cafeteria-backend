from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: Annotated[str, Field(max_length=255)]


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    name: Annotated[Optional[str], Field(max_length=255)] = None


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
