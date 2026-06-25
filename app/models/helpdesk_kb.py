"""Модели схемы helpdesk — база знаний (/kb) и обучение (/train)."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.users import Base


class KbProgressStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    studied = "studied"
    completed = "completed"


class KbQuestionSelectionMode(str, Enum):
    single = "single"
    multiple = "multiple"


class KbQuizAttemptType(str, Enum):
    kb_topic = "kb_topic"
    train_course = "train_course"
    daily_warmup = "daily_warmup"


class KbQuizAttemptStatus(str, Enum):
    in_progress = "in_progress"
    finished = "finished"
    abandoned = "abandoned"


class KbContentFormat(str, Enum):
    html = "html"
    blocks = "blocks"


class KbCourseProgressStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class KbDailyQuizOverrideMode(str, Enum):
    inherit = "inherit"
    required = "required"
    exempt = "exempt"


class KbDailyQuizExemptionAction(str, Enum):
    set_inherit = "set_inherit"
    set_required = "set_required"
    set_exempt = "set_exempt"
    set_exempt_until = "set_exempt_until"


_kb_progress_status = ENUM(
    KbProgressStatus,
    name="kb_progress_status",
    schema="helpdesk",
    create_type=False,
)
_kb_question_selection_mode = ENUM(
    KbQuestionSelectionMode,
    name="kb_question_selection_mode",
    schema="helpdesk",
    create_type=False,
)
_kb_quiz_attempt_type = ENUM(
    KbQuizAttemptType,
    name="kb_quiz_attempt_type",
    schema="helpdesk",
    create_type=False,
)
_kb_quiz_attempt_status = ENUM(
    KbQuizAttemptStatus,
    name="kb_quiz_attempt_status",
    schema="helpdesk",
    create_type=False,
)
_kb_content_format = ENUM(
    KbContentFormat,
    name="kb_content_format",
    schema="helpdesk",
    create_type=False,
)
_kb_course_progress_status = ENUM(
    KbCourseProgressStatus,
    name="kb_course_progress_status",
    schema="helpdesk",
    create_type=False,
)
_kb_daily_quiz_override_mode = ENUM(
    KbDailyQuizOverrideMode,
    name="kb_daily_quiz_override_mode",
    schema="helpdesk",
    create_type=False,
)
_kb_daily_quiz_exemption_action = ENUM(
    KbDailyQuizExemptionAction,
    name="kb_daily_quiz_exemption_action",
    schema="helpdesk",
    create_type=False,
)


class KbCategory(Base):
    __tablename__ = "kb_categories"
    __table_args__ = (
        Index(
            "idx_kb_categories_parent_sort",
            "parent_id",
            "sort_order",
            "id",
            postgresql_where=text("is_active"),
        ),
        Index(
            "uq_kb_categories_slug",
            "slug",
            unique=True,
            postgresql_where=text("slug IS NOT NULL"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_categories.id", ondelete="RESTRICT"),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    parent: Mapped[Optional["KbCategory"]] = relationship(
        "KbCategory",
        remote_side="KbCategory.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list["KbCategory"]] = relationship(
        "KbCategory",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    articles: Mapped[list["KbArticle"]] = relationship(
        "KbArticle",
        back_populates="category",
    )


class KbArticle(Base):
    __tablename__ = "kb_articles"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_kb_articles_slug"),
        Index(
            "idx_kb_articles_category_sort",
            "category_id",
            "sort_order",
            "id",
            postgresql_where=text("is_published"),
        ),
        Index(
            "idx_kb_articles_search",
            "search_vector",
            postgresql_using="gin",
            postgresql_where=text("is_published"),
        ),
        Index(
            "idx_kb_articles_slug",
            "slug",
            postgresql_where=text("is_published"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''"))
    content_html: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    content_format: Mapped[KbContentFormat] = mapped_column(
        _kb_content_format,
        nullable=False,
        server_default=text("'html'::helpdesk.kb_content_format"),
    )
    sidebar_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pass_score_percent: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("100")
    )
    max_attempts: Mapped[Optional[int]] = mapped_column(SmallInteger)
    quiz_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(summary, ''))",
            persisted=True,
        ),
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    category: Mapped["KbCategory"] = relationship("KbCategory", back_populates="articles")
    versions: Mapped[list["KbArticleVersion"]] = relationship(
        "KbArticleVersion",
        back_populates="article",
    )
    quiz: Mapped[Optional["KbQuiz"]] = relationship(
        "KbQuiz",
        back_populates="article",
        uselist=False,
    )
    progress_records: Mapped[list["KbArticleProgress"]] = relationship(
        "KbArticleProgress",
        back_populates="article",
    )
    quiz_attempts: Mapped[list["KbQuizAttempt"]] = relationship(
        "KbQuizAttempt",
        back_populates="article",
    )
    course_links: Mapped[list["KbCourseArticle"]] = relationship(
        "KbCourseArticle",
        back_populates="article",
    )


class KbArticleVersion(Base):
    __tablename__ = "kb_article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version", name="uq_kb_article_versions_article_version"),
        Index("idx_kb_article_versions_article", "article_id", text("version DESC")),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    sidebar_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    article: Mapped["KbArticle"] = relationship("KbArticle", back_populates="versions")


class KbQuiz(Base):
    __tablename__ = "kb_quizzes"
    __table_args__ = (
        UniqueConstraint("article_id", name="uq_kb_quizzes_article"),
        Index(
            "idx_kb_quizzes_article",
            "article_id",
            postgresql_where=text("is_active"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    passing_score_percent: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("100")
    )
    questions_per_attempt: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    article: Mapped["KbArticle"] = relationship("KbArticle", back_populates="quiz")
    questions: Mapped[list["KbQuestion"]] = relationship(
        "KbQuestion",
        back_populates="quiz",
    )
    attempts: Mapped[list["KbQuizAttempt"]] = relationship(
        "KbQuizAttempt",
        back_populates="quiz",
    )
    daily_policies: Mapped[list["KbDailyQuizPolicy"]] = relationship(
        "KbDailyQuizPolicy",
        back_populates="quiz",
    )


class KbQuestion(Base):
    __tablename__ = "kb_questions"
    __table_args__ = (
        Index(
            "idx_kb_questions_quiz_sort",
            "quiz_id",
            "sort_order",
            "id",
            postgresql_where=text("is_active"),
        ),
        Index("idx_kb_questions_tags", "tags", postgresql_using="gin"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''"))
    selection_mode: Mapped[KbQuestionSelectionMode] = mapped_column(
        _kb_question_selection_mode,
        nullable=False,
        server_default=text("'single'::helpdesk.kb_question_selection_mode"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    quiz: Mapped["KbQuiz"] = relationship("KbQuiz", back_populates="questions")
    options: Mapped[list["KbQuestionOption"]] = relationship(
        "KbQuestionOption",
        back_populates="question",
    )
    attempt_answers: Mapped[list["KbQuizAttemptAnswer"]] = relationship(
        "KbQuizAttemptAnswer",
        back_populates="question",
    )


class KbQuestionOption(Base):
    __tablename__ = "kb_question_options"
    __table_args__ = (
        Index("idx_kb_question_options_question_sort", "question_id", "sort_order", "id"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    question: Mapped["KbQuestion"] = relationship("KbQuestion", back_populates="options")


class KbArticleProgress(Base):
    __tablename__ = "kb_article_progress"
    __table_args__ = (
        UniqueConstraint(
            "operator_id",
            "article_id",
            name="uq_kb_article_progress_operator_article",
        ),
        Index("idx_kb_article_progress_operator_status", "operator_id", "status"),
        Index("idx_kb_article_progress_operator_article", "operator_id", "article_id"),
        Index("idx_kb_article_progress_article", "article_id", "status"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[KbProgressStatus] = mapped_column(
        _kb_progress_status,
        nullable=False,
        server_default=text("'not_started'::helpdesk.kb_progress_status"),
    )
    studied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    quiz_passed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_attempt_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_quiz_attempts.id", ondelete="SET NULL"),
    )
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    article: Mapped["KbArticle"] = relationship("KbArticle", back_populates="progress_records")
    last_attempt: Mapped[Optional["KbQuizAttempt"]] = relationship(
        "KbQuizAttempt",
        back_populates="article_progress_links",
        foreign_keys=[last_attempt_id],
    )


class KbQuizAttempt(Base):
    __tablename__ = "kb_quiz_attempts"
    __table_args__ = (
        Index(
            "idx_kb_quiz_attempts_operator_finished",
            "operator_id",
            text("finished_at DESC NULLS LAST"),
        ),
        Index(
            "idx_kb_quiz_attempts_article_finished",
            "article_id",
            text("finished_at DESC NULLS LAST"),
            postgresql_where=text("status = 'finished'"),
        ),
        Index(
            "idx_kb_quiz_attempts_type_operator",
            "attempt_type",
            "operator_id",
            text("started_at DESC"),
        ),
        Index(
            "uq_kb_quiz_attempts_daily_session",
            "operator_id",
            "session_date",
            unique=True,
            postgresql_where=text(
                "attempt_type = 'daily_warmup' "
                "AND session_date IS NOT NULL "
                "AND status IN ('in_progress', 'finished')"
            ),
        ),
        Index("idx_kb_quiz_attempts_quiz", "quiz_id", text("started_at DESC")),
        Index(
            "idx_kb_quiz_attempts_course",
            "course_id",
            "operator_id",
            postgresql_where=text("course_id IS NOT NULL"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_quizzes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_articles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_courses.id", ondelete="SET NULL"),
    )
    attempt_type: Mapped[KbQuizAttemptType] = mapped_column(
        _kb_quiz_attempt_type,
        nullable=False,
        server_default=text("'kb_topic'::helpdesk.kb_quiz_attempt_type"),
    )
    status: Mapped[KbQuizAttemptStatus] = mapped_column(
        _kb_quiz_attempt_status,
        nullable=False,
        server_default=text("'in_progress'::helpdesk.kb_quiz_attempt_status"),
    )
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    total_questions: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    correct_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    session_date: Mapped[Optional[date]] = mapped_column(Date)
    daily_policy_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_daily_quiz_policies.id", ondelete="SET NULL"),
    )
    daily_policy_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    quiz: Mapped["KbQuiz"] = relationship("KbQuiz", back_populates="attempts")
    daily_policy: Mapped[Optional["KbDailyQuizPolicy"]] = relationship(
        "KbDailyQuizPolicy",
        back_populates="attempts",
    )
    article: Mapped["KbArticle"] = relationship("KbArticle", back_populates="quiz_attempts")
    course: Mapped[Optional["KbCourse"]] = relationship("KbCourse", back_populates="quiz_attempts")
    answers: Mapped[list["KbQuizAttemptAnswer"]] = relationship(
        "KbQuizAttemptAnswer",
        back_populates="attempt",
    )
    article_progress_links: Mapped[list["KbArticleProgress"]] = relationship(
        "KbArticleProgress",
        back_populates="last_attempt",
        foreign_keys=[KbArticleProgress.last_attempt_id],
    )


class KbQuizAttemptAnswer(Base):
    __tablename__ = "kb_quiz_attempt_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_kb_quiz_attempt_answers_attempt_question",
        ),
        Index("idx_kb_quiz_attempt_answers_attempt", "attempt_id"),
        Index("idx_kb_quiz_attempt_answers_question_correct", "question_id", "is_correct"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_option_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), nullable=False, server_default=text("'{}'::bigint[]")
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    attempt: Mapped["KbQuizAttempt"] = relationship("KbQuizAttempt", back_populates="answers")
    question: Mapped["KbQuestion"] = relationship("KbQuestion", back_populates="attempt_answers")


class KbDailyQuizPolicy(Base):
    __tablename__ = "kb_daily_quiz_policies"
    __table_args__ = (
        Index(
            "uq_kb_daily_quiz_policies_one_active",
            text("TRUE"),
            unique=True,
            postgresql_where=text("is_active"),
        ),
        Index("idx_kb_daily_quiz_policies_quiz", "quiz_id"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    weekdays: Mapped[list[int]] = mapped_column(
        ARRAY(SmallInteger),
        nullable=False,
        server_default=text("'{1,2,3,4,5,6,7}'::smallint[]"),
    )
    timezone: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'Europe/Moscow'")
    )
    show_from_time: Mapped[Optional[time]] = mapped_column(Time)
    show_until_time: Mapped[Optional[time]] = mapped_column(Time)
    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_quizzes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    questions_per_session: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("5")
    )
    passing_score_percent: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("100")
    )
    is_blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    allow_skip: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    require_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="SET NULL"),
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    quiz: Mapped["KbQuiz"] = relationship("KbQuiz", back_populates="daily_policies")
    attempts: Mapped[list["KbQuizAttempt"]] = relationship(
        "KbQuizAttempt",
        back_populates="daily_policy",
    )


class KbOperatorDailyQuizSettings(Base):
    __tablename__ = "kb_operator_daily_quiz_settings"
    __table_args__ = (
        Index("idx_kb_operator_daily_quiz_settings_mode", "override_mode"),
        Index(
            "idx_kb_operator_daily_quiz_settings_exempt_until",
            "exempt_until",
            postgresql_where=text("exempt_until IS NOT NULL"),
        ),
        {"schema": "helpdesk"},
    )

    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    override_mode: Mapped[KbDailyQuizOverrideMode] = mapped_column(
        _kb_daily_quiz_override_mode,
        nullable=False,
        server_default=text("'inherit'::helpdesk.kb_daily_quiz_override_mode"),
    )
    exempt_until: Mapped[Optional[date]] = mapped_column(Date)
    exempt_reason: Mapped[Optional[str]] = mapped_column(Text)
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class KbDailyQuizExemptionLog(Base):
    __tablename__ = "kb_daily_quiz_exemption_log"
    __table_args__ = (
        Index(
            "idx_kb_daily_quiz_exemption_log_operator",
            "operator_id",
            text("changed_at DESC"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[KbDailyQuizExemptionAction] = mapped_column(
        _kb_daily_quiz_exemption_action,
        nullable=False,
    )
    override_mode: Mapped[Optional[KbDailyQuizOverrideMode]] = mapped_column(
        _kb_daily_quiz_override_mode,
    )
    exempt_until: Mapped[Optional[date]] = mapped_column(Date)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="SET NULL"),
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class KbCourse(Base):
    __tablename__ = "kb_courses"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_kb_courses_slug"),
        Index(
            "idx_kb_courses_active_sort",
            "sort_order",
            "id",
            postgresql_where=text("is_active"),
        ),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    articles: Mapped[list["KbCourseArticle"]] = relationship(
        "KbCourseArticle",
        back_populates="course",
    )
    progress_records: Mapped[list["KbCourseProgress"]] = relationship(
        "KbCourseProgress",
        back_populates="course",
    )
    quiz_attempts: Mapped[list["KbQuizAttempt"]] = relationship(
        "KbQuizAttempt",
        back_populates="course",
    )


class KbCourseArticle(Base):
    __tablename__ = "kb_course_articles"
    __table_args__ = (
        UniqueConstraint("course_id", "article_id", name="uq_kb_course_articles_course_article"),
        Index("idx_kb_course_articles_course_sort", "course_id", "sort_order", "id"),
        Index("idx_kb_course_articles_article", "article_id"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_articles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    course: Mapped["KbCourse"] = relationship("KbCourse", back_populates="articles")
    article: Mapped["KbArticle"] = relationship("KbArticle", back_populates="course_links")


class KbCourseProgress(Base):
    __tablename__ = "kb_course_progress"
    __table_args__ = (
        UniqueConstraint(
            "operator_id",
            "course_id",
            name="uq_kb_course_progress_operator_course",
        ),
        Index("idx_kb_course_progress_operator", "operator_id", "status"),
        Index("idx_kb_course_progress_course", "course_id", "status"),
        {"schema": "helpdesk"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.skystream_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("helpdesk.kb_courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[KbCourseProgressStatus] = mapped_column(
        _kb_course_progress_status,
        nullable=False,
        server_default=text("'not_started'::helpdesk.kb_course_progress_status"),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_articles_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    required_articles_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    course: Mapped["KbCourse"] = relationship("KbCourse", back_populates="progress_records")
