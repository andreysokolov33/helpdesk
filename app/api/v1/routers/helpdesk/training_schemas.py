"""Pydantic-схемы тренажёра (/train)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.api.v1.routers.helpdesk.kb_schemas import KbQuizQuestionPublic

TrainingSourceType = Literal["daily", "article"]
TrainingSessionStatus = Literal["in_progress", "finished", "abandoned"]


# ---------------------------------------------------------------------------
# Источники
# ---------------------------------------------------------------------------


class TrainingDailySource(BaseModel):
    available: bool
    title: str
    questions_count: int = 0


class TrainingArticleSource(BaseModel):
    id: int
    slug: str
    title: str
    questions_count: int


class TrainingCategorySource(BaseModel):
    id: int
    title: str
    questions_count: int
    articles: list[TrainingArticleSource] = Field(default_factory=list)


class TrainingAllArticlesSource(BaseModel):
    questions_count: int
    articles_count: int


class TrainingSourcesResponse(BaseModel):
    daily: TrainingDailySource
    all_articles: TrainingAllArticlesSource
    categories: list[TrainingCategorySource] = Field(default_factory=list)
    inactivity_minutes: int


# ---------------------------------------------------------------------------
# Сессия оператора
# ---------------------------------------------------------------------------


class TrainingStartRequest(BaseModel):
    source_type: TrainingSourceType
    article_id: int | None = Field(None, ge=1)
    category_id: int | None = Field(None, ge=1)
    all_articles: bool = False

    @model_validator(mode="after")
    def _check_source(self) -> "TrainingStartRequest":
        if self.source_type == "article":
            chosen = [self.article_id is not None, self.category_id is not None, self.all_articles]
            if sum(chosen) != 1:
                raise ValueError(
                    "Для source_type=article укажите article_id, category_id либо all_articles=true"
                )
        elif self.article_id is not None or self.category_id is not None or self.all_articles:
            raise ValueError("Для source_type=daily article_id, category_id и all_articles не указываются")
        return self


class TrainingArticleLink(BaseModel):
    id: int
    slug: str
    title: str


class TrainingSessionState(BaseModel):
    id: int
    source_type: TrainingSourceType
    source_title: str
    source_kind_label: str
    article_id: int | None = None
    category_id: int | None = None
    status: TrainingSessionStatus
    started_at: datetime
    last_answer_at: datetime | None = None
    finished_at: datetime | None = None
    total_answers: int
    correct_count: int
    wrong_count: int
    score_percent: float
    duration_sec: int
    inactivity_minutes: int


class TrainingActiveSessionResponse(BaseModel):
    session: TrainingSessionState | None = None


class TrainingNextQuestionResponse(BaseModel):
    session: TrainingSessionState
    question: KbQuizQuestionPublic | None = None
    round_no: int = 0
    round_position: int = 0
    pool_size: int = 0


class TrainingSubmitAnswerRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    selected_option_ids: list[int] = Field(..., min_length=1, max_length=20)


class TrainingSubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_option_ids: list[int] = Field(default_factory=list)
    explanation: str | None = None
    article: TrainingArticleLink | None = None
    completed: bool = False
    session: TrainingSessionState


class TrainingSessionListItem(BaseModel):
    id: int
    source_type: TrainingSourceType
    source_title: str
    source_kind_label: str
    status: TrainingSessionStatus
    started_at: datetime
    last_answer_at: datetime | None = None
    finished_at: datetime | None = None
    total_answers: int
    correct_count: int
    wrong_count: int
    score_percent: float
    duration_sec: int


class TrainingTotals(BaseModel):
    sessions_count: int = 0
    total_answers: int = 0
    correct_count: int = 0
    score_percent: float = 0.0
    total_duration_sec: int = 0


class TrainingMySessionsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    totals: TrainingTotals
    items: list[TrainingSessionListItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Администратор
# ---------------------------------------------------------------------------


class TrainingAdminSummaryResponse(BaseModel):
    date_from: date
    date_to: date
    operators_count: int
    active_operators_count: int
    sessions_count: int
    total_answers: int
    correct_count: int
    avg_score_percent: float
    total_duration_sec: int
    coverage: int


class TrainingLeaderItem(BaseModel):
    rank: int
    operator_id: int
    operator_name: str
    correct: int
    total: int
    raw_percent: float
    score_percent: float
    coverage: int
    low_data: bool


class TrainingLeadersResponse(BaseModel):
    date_from: date
    date_to: date
    k: float
    p0_percent: float
    low_data_threshold: int
    items: list[TrainingLeaderItem] = Field(default_factory=list)


class TrainingAdminOperatorRow(BaseModel):
    operator_id: int
    operator_name: str
    sessions_count: int
    total_answers: int
    correct_count: int
    score_percent: float | None = None
    coverage: int
    total_duration_sec: int
    last_activity_at: datetime | None = None
    has_active_session: bool = False


class TrainingAdminOperatorsResponse(BaseModel):
    date_from: date
    date_to: date
    items: list[TrainingAdminOperatorRow] = Field(default_factory=list)


class TrainingAdminOperatorSessionsResponse(BaseModel):
    date_from: date
    date_to: date
    operator_id: int
    operator_name: str
    page: int
    per_page: int
    total: int
    items: list[TrainingSessionListItem] = Field(default_factory=list)
