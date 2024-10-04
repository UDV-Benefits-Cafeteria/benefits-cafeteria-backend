from typing import Annotated, Optional

from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    name: Annotated[str, Field(max_length=255)]


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Annotated[Optional[str], Field(max_length=255)] = None


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
