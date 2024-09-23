from typing import Optional, TYPE_CHECKING

from sqlalchemy import Text, Integer, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from db.db import Base

if TYPE_CHECKING:
    from models import Benefit, User

class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    benefit_id: Mapped[int] = mapped_column(ForeignKey('benefits.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    text: Mapped[Text] = mapped_column(Text)

    benefit: Mapped['Benefit'] = relationship('Benefit', back_populates='questions')
    user: Mapped['User'] = relationship('User', back_populates='questions')
    answer: Mapped['Answer'] = relationship('Answer', back_populates='question', uselist=False)


class Answer(Base):
    __tablename__ = 'answers'

    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)
    hr_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    text: Mapped[Text] = mapped_column(Text)

    hr: Mapped[Optional['User']] = relationship('User', back_populates='answers')
    question: Mapped['Question'] = relationship('Question', back_populates='answer', uselist=False)


