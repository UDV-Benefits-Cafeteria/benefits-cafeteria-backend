from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.db import Base

if TYPE_CHECKING:
    from models import Benefit, User


class Question(Base):
    __tablename__ = "questions"

    repr_cols = ("id", "benefit_id", "user_id", "text")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(ForeignKey("benefits.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[Text] = mapped_column(Text, nullable=False)

    benefit: Mapped["Benefit"] = relationship("Benefit", back_populates="questions")
    user: Mapped["User"] = relationship("User", back_populates="questions")
    answer: Mapped["Answer"] = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    repr_cols = ("question_id", "hr_id", "text")

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    hr_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[Text] = mapped_column(Text, nullable=False)

    hr: Mapped[Optional["User"]] = relationship("User", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answer")
