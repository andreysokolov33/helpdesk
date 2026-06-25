"""Схемы ежедневного теста операторов."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.api.v1.routers.helpdesk.kb_schemas import (
    KbQuizAnsweredState,
    KbQuizFinishResponse,
    KbQuizQuestionPublic,
    KbQuizStartAttemptResponse,
    KbQuizSubmitAnswerResponse,
)


class DailyQuizHistoryItem(BaseModel):
    session_date: date
    day_label: str
    passed: bool | None = None
    status: str
    correct_count: int = 0
    total_questions: int = 0


class DailyQuizStatusResponse(BaseModel):
    required: bool
    show_modal: bool
    session_date: date | None = None
    attempt_id: int | None = None
    attempt_status: str = "none"
    title: str | None = None
    questions_per_session: int | None = None
    history: list[DailyQuizHistoryItem] = Field(default_factory=list)


class DailyQuizSessionResponse(BaseModel):
    quiz_id: int
    article_id: int
    title: str
    passing_score_percent: int
    session_date: date
    attempt_id: int | None = None
    attempt_status: str = "none"
    passed: bool | None = None
    total_questions: int
    correct_count: int | None = None
    questions: list[KbQuizQuestionPublic] = Field(default_factory=list)
    answered: list[KbQuizAnsweredState] = Field(default_factory=list)


# Re-export для роутера
DailyQuizFinishResponse = KbQuizFinishResponse
DailyQuizStartAttemptResponse = KbQuizStartAttemptResponse
DailyQuizSubmitAnswerResponse = KbQuizSubmitAnswerResponse
