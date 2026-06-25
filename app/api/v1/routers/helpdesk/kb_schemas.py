"""Pydantic-схемы базы знаний (/kb)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

KbReadStatus = Literal["unread", "reading", "read"]
KbQuizStatus = Literal["none", "not_started", "in_progress", "passed", "failed"]


class KbArticleListItem(BaseModel):
    id: int
    slug: str
    title: str
    subtitle: str | None = None
    summary: str | None = None
    category_id: int
    category_title: str
    has_quiz: bool = False
    read_status: KbReadStatus = "unread"
    quiz_status: KbQuizStatus = "none"
    quiz_correct_count: int | None = None
    quiz_total_questions: int | None = None
    quiz_error_count: int | None = None
    quiz_passed_at: datetime | None = None
    quiz_finished_at: datetime | None = None


class KbCategorySection(BaseModel):
    id: int
    title: str
    slug: str | None = None
    sort_order: int
    articles: list[KbArticleListItem] = Field(default_factory=list)


class KbHomeResponse(BaseModel):
    categories: list[KbCategorySection]
    total_articles: int


class KbSearchResponse(BaseModel):
    query: str
    items: list[KbArticleListItem]


class KbArticleDetailResponse(BaseModel):
    id: int
    slug: str
    title: str
    subtitle: str | None = None
    summary: str | None = None
    content_html: str
    sidebar_json: dict = Field(default_factory=dict)
    category_id: int
    category_title: str
    has_quiz: bool = False
    quiz_id: int | None = None
    read_status: KbReadStatus = "unread"
    quiz_status: KbQuizStatus = "none"
    quiz_correct_count: int | None = None
    quiz_total_questions: int | None = None
    quiz_error_count: int | None = None
    quiz_passed_at: datetime | None = None
    quiz_finished_at: datetime | None = None
    published_at: datetime | None = None


class KbMarkStudiedResponse(BaseModel):
    article_id: int
    read_status: KbReadStatus
    studied_at: datetime | None = None


class KbQuizOptionPublic(BaseModel):
    id: int
    option_text: str
    sort_order: int


class KbQuizQuestionPublic(BaseModel):
    id: int
    question_text: str
    selection_mode: Literal["single", "multiple"]
    sort_order: int
    options: list[KbQuizOptionPublic] = Field(default_factory=list)


class KbQuizAnsweredState(BaseModel):
    question_id: int
    selected_option_ids: list[int]
    is_correct: bool
    correct_option_ids: list[int] = Field(default_factory=list)


class KbQuizSessionResponse(BaseModel):
    quiz_id: int
    article_id: int
    title: str
    passing_score_percent: int
    attempt_id: int | None = None
    attempt_status: Literal["none", "in_progress", "finished"] = "none"
    passed: bool | None = None
    score: int | None = None
    total_questions: int
    correct_count: int | None = None
    questions: list[KbQuizQuestionPublic] = Field(default_factory=list)
    answered: list[KbQuizAnsweredState] = Field(default_factory=list)


class KbQuizStartAttemptResponse(BaseModel):
    attempt_id: int
    total_questions: int


class KbQuizSubmitAnswerRequest(BaseModel):
    question_id: int
    selected_option_ids: list[int] = Field(default_factory=list)


class KbQuizSubmitAnswerResponse(BaseModel):
    is_correct: bool
    explanation: str | None = None
    correct_option_ids: list[int] = Field(default_factory=list)


class KbQuizFinishResponse(BaseModel):
    attempt_id: int
    passed: bool
    score: int
    total_questions: int
    correct_count: int
    error_count: int
    quiz_status: KbQuizStatus
    read_status: KbReadStatus
    quiz_passed_at: datetime | None = None
    quiz_finished_at: datetime | None = None
