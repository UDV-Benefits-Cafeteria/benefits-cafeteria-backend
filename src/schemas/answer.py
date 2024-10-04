from typing import Optional

from pydantic import BaseModel, ConfigDict


class AnswerBase(BaseModel):
    text: str
    user_id: Optional[int] = None


class AnswerCreate(AnswerBase):
    pass


class AnswerUpdate(AnswerBase):
    text: Optional[str] = None


class AnswerRead(AnswerBase):
    question_id: int

    model_config = ConfigDict(from_attributes=True)
