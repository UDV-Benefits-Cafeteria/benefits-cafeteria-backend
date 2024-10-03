from typing import Annotated, Optional

from pydantic import BaseModel, Field, ConfigDict


class PositionBase(BaseModel):
    name: Annotated[str, Field(max_length=150)]


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    name: Annotated[Optional[str], Field(max_length=150)] = None

class PositionRead(PositionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

