from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PositionBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=150)]

    @field_validator("name")
    @classmethod
    def name_to_lower(cls, name: str) -> str:
        return name.lower()


class PositionCreate(PositionBase):
    pass


class PositionUpdate(PositionBase):
    name: Annotated[Optional[str], Field(min_length=2, max_length=150)] = None


class PositionRead(PositionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
