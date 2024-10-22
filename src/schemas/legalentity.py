from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field


class LegalEntityBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255)]


class LegalEntityCreate(LegalEntityBase):
    pass


class LegalEntityUpdate(LegalEntityBase):
    name: Annotated[Optional[str], Field(min_length=2, max_length=255)] = None


class LegalEntityRead(LegalEntityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
