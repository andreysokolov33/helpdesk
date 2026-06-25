"""Статистика тестирования оператора (БЗ + ежедневные тесты)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.daily_quiz_service import operator_requires_daily_quiz

_SCHEMA = "helpdesk"
_PRACTICE_FILTER = (
    " AND COALESCE(qa.daily_policy_snapshot->>'practice', 'false') <> 'true'"
)


def _day_label(
    *,
    session_date: date | datetime | None,
    finished_at: datetime | None,
) -> str:
    if session_date is not None:
        d = session_date.date() if isinstance(session_date, datetime) else session_date
        return str(int(d.day))
    if finished_at is not None:
        return str(int(finished_at.day))
    return "?"


def _score_percent(correct: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(round((correct / total) * 100))


def _empty_response(*, eligible: bool) -> dict[str, Any]:
    empty = {
        "attempts_count": 0,
        "passed_count": 0,
        "avg_score_percent": 0.0,
    }
    return {
        "eligible": eligible,
        "kb_overall": {**empty, "articles_with_quiz": 0, "articles_passed": 0},
        "daily_overall": empty,
        "categories": [],
        "kb_attempts": [],
        "daily_attempts": [],
    }


async def fetch_operator_quiz_stats(
    db: AsyncSession,
    *,
    operator_id: int,
    role: str | None,
    level: int | None,
) -> dict[str, Any]:
    eligible = operator_requires_daily_quiz(role=role, level=level)
    if not eligible:
        return _empty_response(eligible=False)

    kb_overall_row = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(*)::int AS attempts_count,
                    COUNT(*) FILTER (WHERE qa.passed IS TRUE)::int AS passed_count,
                    COALESCE(
                        AVG(
                            qa.correct_count::float
                            / NULLIF(qa.total_questions, 0)
                            * 100.0
                        ),
                        0
                    ) AS avg_score_percent
                FROM {_SCHEMA}.kb_quiz_attempts qa
                WHERE qa.operator_id = :operator_id
                  AND qa.attempt_type = 'kb_topic'
                  AND qa.status = 'finished'
                  {_PRACTICE_FILTER}
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().first()

    articles_row = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(DISTINCT a.id)::int AS articles_with_quiz,
                    COUNT(DISTINCT p.article_id) FILTER (
                        WHERE p.quiz_passed_at IS NOT NULL
                    )::int AS articles_passed
                FROM {_SCHEMA}.kb_articles a
                JOIN {_SCHEMA}.kb_quizzes q
                    ON q.article_id = a.id AND q.is_active IS TRUE
                LEFT JOIN {_SCHEMA}.kb_article_progress p
                    ON p.article_id = a.id AND p.operator_id = :operator_id
                WHERE a.is_published IS TRUE
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().first()

    daily_overall_row = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(*)::int AS attempts_count,
                    COUNT(*) FILTER (WHERE qa.passed IS TRUE)::int AS passed_count,
                    COALESCE(
                        AVG(
                            qa.correct_count::float
                            / NULLIF(qa.total_questions, 0)
                            * 100.0
                        ),
                        0
                    ) AS avg_score_percent
                FROM {_SCHEMA}.kb_quiz_attempts qa
                WHERE qa.operator_id = :operator_id
                  AND qa.attempt_type = 'daily_warmup'
                  AND qa.status = 'finished'
                  AND qa.session_date IS NOT NULL
                  {_PRACTICE_FILTER}
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().first()

    category_rows = (
        await db.execute(
            text(
                f"""
                WITH latest_article_attempt AS (
                    SELECT DISTINCT ON (qa.article_id)
                        qa.article_id,
                        qa.correct_count,
                        qa.total_questions,
                        qa.passed
                    FROM {_SCHEMA}.kb_quiz_attempts qa
                    WHERE qa.operator_id = :operator_id
                      AND qa.attempt_type = 'kb_topic'
                      AND qa.status = 'finished'
                      {_PRACTICE_FILTER}
                    ORDER BY qa.article_id, qa.finished_at DESC
                )
                SELECT
                    c.id AS category_id,
                    c.title AS category_title,
                    COUNT(DISTINCT a.id) FILTER (WHERE q.id IS NOT NULL)::int AS articles_with_quiz,
                    COUNT(DISTINCT p.article_id) FILTER (
                        WHERE p.quiz_passed_at IS NOT NULL
                    )::int AS articles_passed,
                    COUNT(la.article_id)::int AS articles_attempted,
                    COALESCE(
                        AVG(
                            la.correct_count::float
                            / NULLIF(la.total_questions, 0)
                            * 100.0
                        ),
                        0
                    ) AS avg_score_percent,
                    COUNT(la.article_id) FILTER (WHERE la.passed IS TRUE)::int AS passed_attempts
                FROM {_SCHEMA}.kb_categories c
                JOIN {_SCHEMA}.kb_articles a
                    ON a.category_id = c.id AND a.is_published IS TRUE
                LEFT JOIN {_SCHEMA}.kb_quizzes q
                    ON q.article_id = a.id AND q.is_active IS TRUE
                LEFT JOIN {_SCHEMA}.kb_article_progress p
                    ON p.article_id = a.id AND p.operator_id = :operator_id
                LEFT JOIN latest_article_attempt la
                    ON la.article_id = a.id
                GROUP BY c.id, c.title, c.sort_order
                HAVING COUNT(DISTINCT a.id) FILTER (WHERE q.id IS NOT NULL) > 0
                ORDER BY c.sort_order, c.title
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().all()

    kb_attempt_rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    qa.id AS attempt_id,
                    qa.attempt_type::text AS attempt_type,
                    qa.finished_at,
                    qa.correct_count,
                    qa.total_questions,
                    qa.passed,
                    a.slug AS article_slug,
                    a.title AS article_title,
                    c.title AS category_title
                FROM {_SCHEMA}.kb_quiz_attempts qa
                JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                JOIN {_SCHEMA}.kb_categories c ON c.id = a.category_id
                WHERE qa.operator_id = :operator_id
                  AND qa.attempt_type = 'kb_topic'
                  AND qa.status = 'finished'
                  {_PRACTICE_FILTER}
                ORDER BY qa.finished_at DESC NULLS LAST
                LIMIT 14
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().all()

    daily_attempt_rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    qa.id AS attempt_id,
                    qa.attempt_type::text AS attempt_type,
                    qa.finished_at,
                    qa.session_date,
                    qa.correct_count,
                    qa.total_questions,
                    qa.passed,
                    COALESCE(p.title, a.title, 'Ежедневный тест') AS article_title
                FROM {_SCHEMA}.kb_quiz_attempts qa
                LEFT JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                LEFT JOIN {_SCHEMA}.kb_daily_quiz_policies p
                    ON p.id = qa.daily_policy_id
                WHERE qa.operator_id = :operator_id
                  AND qa.attempt_type = 'daily_warmup'
                  AND qa.status = 'finished'
                  AND qa.session_date IS NOT NULL
                  {_PRACTICE_FILTER}
                ORDER BY qa.session_date DESC NULLS LAST, qa.finished_at DESC NULLS LAST
                LIMIT 14
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().all()

    def _attempt_item(row: dict[str, Any]) -> dict[str, Any]:
        correct = int(row.get("correct_count") or 0)
        total = int(row.get("total_questions") or 0)
        sd = row.get("session_date")
        if isinstance(sd, datetime):
            sd = sd.date()
        return {
            "attempt_id": int(row["attempt_id"]),
            "attempt_type": str(row["attempt_type"]),
            "finished_at": row.get("finished_at"),
            "session_date": sd,
            "day_label": _day_label(session_date=sd, finished_at=row.get("finished_at")),
            "article_slug": row.get("article_slug"),
            "article_title": row.get("article_title"),
            "category_title": row.get("category_title"),
            "correct_count": correct,
            "total_questions": total,
            "score_percent": _score_percent(correct, total),
            "passed": bool(row.get("passed")),
        }

    kb_overall = dict(kb_overall_row or {})
    daily_overall = dict(daily_overall_row or {})
    articles = dict(articles_row or {})

    return {
        "eligible": True,
        "kb_overall": {
            "attempts_count": int(kb_overall.get("attempts_count") or 0),
            "passed_count": int(kb_overall.get("passed_count") or 0),
            "avg_score_percent": round(float(kb_overall.get("avg_score_percent") or 0), 1),
            "articles_with_quiz": int(articles.get("articles_with_quiz") or 0),
            "articles_passed": int(articles.get("articles_passed") or 0),
        },
        "daily_overall": {
            "attempts_count": int(daily_overall.get("attempts_count") or 0),
            "passed_count": int(daily_overall.get("passed_count") or 0),
            "avg_score_percent": round(float(daily_overall.get("avg_score_percent") or 0), 1),
        },
        "categories": [
            {
                "category_id": int(r["category_id"]),
                "category_title": str(r["category_title"]),
                "articles_with_quiz": int(r["articles_with_quiz"] or 0),
                "articles_passed": int(r["articles_passed"] or 0),
                "articles_attempted": int(r["articles_attempted"] or 0),
                "avg_score_percent": round(float(r["avg_score_percent"] or 0), 1),
                "passed_attempts": int(r["passed_attempts"] or 0),
            }
            for r in category_rows
        ],
        "kb_attempts": [_attempt_item(dict(r)) for r in kb_attempt_rows],
        "daily_attempts": [_attempt_item(dict(r)) for r in daily_attempt_rows],
    }
