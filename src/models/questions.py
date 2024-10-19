from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Benefit, User


class Question(Base):
    """
    Represents a question asked about a benefit.

    This class maps to the 'questions' table in the database and includes
    attributes for the question's unique identifier, associated benefit,
    user who asked, and the question text.

    Attributes:
        id (int): The unique identifier for the question.
        benefit_id (Optional[int]): The identifier of the benefit associated with the question.
        user_id (Optional[int]): The identifier of the user who asked the question.
        text (Text): The content of the question.

    Relationships:
        benefit (Benefit): The benefit associated with this question, linked to the Benefit model.
        user (User): The user who asked, linked to the User model.
        answer (Answer): The answer to this question, linked to the Answer model.
    """

    __tablename__ = "questions"

    repr_cols = ("id", "benefit_id", "user_id", "text")

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("benefits.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[Text] = mapped_column(Text, nullable=False)

    benefit: Mapped[Optional["Benefit"]] = relationship(
        "Benefit", back_populates="questions"
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="questions")
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan", uselist=False
    )


class Answer(Base):
    """
    Represents an answer to a question.

    This class maps to the 'answers' table in the database and includes
    attributes for the answer's associated question, user who provided the
    answer, and the answer text.

    Attributes:
        question_id (int): The identifier of the question being answered.
        user_id (Optional[int]): The identifier of the user who provided the answer.
        text (Text): The content of the answer.

    Relationships:
        user (User): The user who provided the answer, linked to the User model.
        question (Question): The question this answer responds to, linked to the Question model.
    """

    __tablename__ = "answers"

    repr_cols = ("question_id", "user_id", "text")

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[Text] = mapped_column(Text, nullable=False)

    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="answers",
        foreign_keys=[user_id],
    )
    question: Mapped["Question"] = relationship("Question", back_populates="answer")
