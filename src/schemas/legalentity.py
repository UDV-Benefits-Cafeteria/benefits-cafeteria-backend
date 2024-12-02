from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class LegalEntityBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255)]


class LegalEntityCreate(LegalEntityBase):
    pass


class LegalEntityUpdate(LegalEntityBase):
    pass


class LegalEntityRead(LegalEntityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LegalEntityUploadError(BaseModel):
    row: int
    error: str


class LegalEntityUploadResponse(BaseModel):
    created_entities: list[LegalEntityRead]
    errors: list[LegalEntityUploadError]


class LegalEntityValidationResponse(BaseModel):
    valid_entities: list[LegalEntityCreate]
    errors: list[LegalEntityUploadError]
