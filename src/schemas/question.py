from typing import  Optional

from pydantic import BaseModel,  ConfigDict

from src.schemas.answer import AnswerRead


class QuestionBase(BaseModel):
    text: str
    benefit_id: Optional[int] = None
    user_id: Optional[int] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(QuestionBase):
    text: Optional[str] = None


class QuestionRead(QuestionBase):
    id: int
    answer: Optional["AnswerRead"] = None

    model_config = ConfigDict(from_attributes=True)


