from __future__ import annotations

from pydantic import BaseModel, Field

from app.api.v1.routers.helpdesk.operator_quiz_schemas import (
    OperatorQuizCategoryStat,
    OperatorQuizOverallStats,
)


class SupportOperatorOption(BaseModel):
    id: int
    label: str


class StatsSummaryResponse(BaseModel):
    date_from: str
    date_to: str
    new_tickets: int = 0
    closed_tickets: int = 0
    avg_first_response_sec: float | None = None
    avg_lifetime_sec: float | None = None
    avg_rating: float | None = None
    is_admin_view: bool = False
    operator_id: int | None = None
    operator_name: str | None = None


class OperatorStatsRow(BaseModel):
    operator_id: int
    operator_name: str
    new_tickets: int = 0
    closed_tickets: int = 0
    avg_first_response_sec: float | None = None
    avg_lifetime_sec: float | None = None
    avg_rating: float | None = None


class StatsRatingItem(BaseModel):
    ticket_id: int
    source: str
    source_label: str
    rating: int | None = None
    rating_comment: str | None = None
    rated_at: str | None = None
    lifetime_sec: float | None = None
    category_label: str | None = None
    engineer_involved: bool = False
    assigned_operator_name: str | None = None


class StatsDashboardResponse(BaseModel):
    summary: StatsSummaryResponse
    operators: list[OperatorStatsRow] = Field(default_factory=list)
    recent_ratings: list[StatsRatingItem] = Field(default_factory=list)
    operator_options: list[SupportOperatorOption] = Field(default_factory=list)


class QuizTrainingSummary(BaseModel):
    operators_count: int = 0
    kb_avg_score_percent: float = 0.0
    articles_passed_ratio_percent: float = 0.0
    daily_avg_score_percent: float = 0.0
    daily_pass_rate_percent: float = 0.0
    needs_attention_count: int = 0


class QuizTrainingOperatorRow(BaseModel):
    operator_id: int
    operator_name: str
    kb_articles_with_quiz: int = 0
    kb_articles_passed: int = 0
    kb_avg_score_percent: float = 0.0
    daily_attempts_count: int = 0
    daily_passed_count: int = 0
    daily_avg_score_percent: float = 0.0
    today_daily_passed: bool | None = None
    today_daily_label: str = "—"
    weak_category_title: str | None = None
    needs_attention: bool = False


class QuizTrainingWeakArticle(BaseModel):
    article_id: int
    article_title: str
    article_slug: str | None = None
    category_title: str | None = None
    passed: bool
    score_percent: float


class QuizTrainingOperatorDetail(BaseModel):
    operator_id: int
    operator_name: str
    eligible: bool = True
    kb_overall: OperatorQuizOverallStats = Field(default_factory=OperatorQuizOverallStats)
    daily_overall: OperatorQuizOverallStats = Field(default_factory=OperatorQuizOverallStats)
    categories: list[OperatorQuizCategoryStat] = Field(default_factory=list)
    weak_articles: list[QuizTrainingWeakArticle] = Field(default_factory=list)


class QuizTrainingDashboardResponse(BaseModel):
    date_from: str
    date_to: str
    summary: QuizTrainingSummary
    operators: list[QuizTrainingOperatorRow] = Field(default_factory=list)
    operator_detail: QuizTrainingOperatorDetail | None = None
