"""
This file is made for testing.
"""
from pydantic import BaseModel


class LegalEntitySchemaAdd(BaseModel):
    name: str

    class Config:
        from_attributes = True
