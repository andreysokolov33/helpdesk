from __future__ import annotations

from pydantic import BaseModel, Field


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


class StatsDashboardResponse(BaseModel):
    summary: StatsSummaryResponse
    operators: list[OperatorStatsRow] = Field(default_factory=list)
    recent_ratings: list[StatsRatingItem] = Field(default_factory=list)
    operator_options: list[SupportOperatorOption] = Field(default_factory=list)
