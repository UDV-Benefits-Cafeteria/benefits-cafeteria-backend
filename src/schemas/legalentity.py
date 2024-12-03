from typing import Annotated, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.utils.legal_entity_count import get_legal_entity_counts


class LegalEntityBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255)]


class LegalEntityCreate(LegalEntityBase):
    pass


class LegalEntityUpdate(LegalEntityBase):
    pass


class LegalEntityRead(LegalEntityBase):
    id: int
    employee_count: Optional[int] = None
    staff_count: Optional[int] = None

    @model_validator(mode="before")
    def calculate_counts(self) -> Self:
        employee_number, staff_number = get_legal_entity_counts(self.id)

        self.employee_count = employee_number
        self.staff_count = staff_number

        return self

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
