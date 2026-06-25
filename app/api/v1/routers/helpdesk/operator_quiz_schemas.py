"""Схемы статистики тестирования оператора."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.api.v1.routers.helpdesk.kb_schemas import KbQuizQuestionPublic


class OperatorQuizOverallStats(BaseModel):
    attempts_count: int = 0
    passed_count: int = 0
    avg_score_percent: float = 0.0
    articles_with_quiz: int | None = None
    articles_passed: int | None = None


class OperatorQuizCategoryStat(BaseModel):
    category_id: int
    category_title: str
    articles_with_quiz: int
    articles_passed: int
    articles_attempted: int
    avg_score_percent: float
    passed_attempts: int


class OperatorQuizAttemptItem(BaseModel):
    attempt_id: int
    attempt_type: str
    finished_at: datetime | None = None
    session_date: date | None = None
    day_label: str = "?"
    article_slug: str | None = None
    article_title: str | None = None
    category_title: str | None = None
    correct_count: int
    total_questions: int
    score_percent: int
    passed: bool


class OperatorQuizAnsweredReview(BaseModel):
    question_id: int
    selected_option_ids: list[int]
    is_correct: bool
    correct_option_ids: list[int] = Field(default_factory=list)
    explanation: str | None = None


class OperatorQuizAttemptReviewResponse(BaseModel):
    attempt_id: int
    attempt_type: str
    finished_at: datetime | None = None
    session_date: date | None = None
    article_slug: str | None = None
    article_title: str | None = None
    category_title: str | None = None
    correct_count: int
    total_questions: int
    score_percent: int
    passed: bool
    passing_score_percent: int = 100
    questions: list[KbQuizQuestionPublic] = Field(default_factory=list)
    answered: list[OperatorQuizAnsweredReview] = Field(default_factory=list)


class OperatorQuizPracticeStartResponse(BaseModel):
    attempt_id: int
    total_questions: int


class OperatorQuizStatsResponse(BaseModel):
    eligible: bool
    kb_overall: OperatorQuizOverallStats = Field(default_factory=OperatorQuizOverallStats)
    daily_overall: OperatorQuizOverallStats = Field(default_factory=OperatorQuizOverallStats)
    categories: list[OperatorQuizCategoryStat] = Field(default_factory=list)
    kb_attempts: list[OperatorQuizAttemptItem] = Field(default_factory=list)
    daily_attempts: list[OperatorQuizAttemptItem] = Field(default_factory=list)
