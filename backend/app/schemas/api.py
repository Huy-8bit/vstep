from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.writing import StrictModel


class Credentials(StrictModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ExamCreate(StrictModel):
    mode: Literal["FULL_TEST", "TASK1", "TASK2"]
    question_ids: list[str] = Field(default_factory=list, max_length=2)
    timed: bool = True


class AnswerUpdate(StrictModel):
    answer: str = Field(max_length=20000)
    revision: int = Field(ge=0)


class ExamSubmit(StrictModel):
    answers: dict[str, AnswerUpdate] = Field(default_factory=dict)
