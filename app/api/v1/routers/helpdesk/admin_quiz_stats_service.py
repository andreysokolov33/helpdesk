"""Сводная статистика тестирования операторов для администратора."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk import operator_quiz_stats_service as op_quiz_svc

_SCHEMA = "helpdesk"
_PRACTICE_FILTER = (
    " AND COALESCE(qa.daily_policy_snapshot->>'practice', 'false') <> 'true'"
)


def _score_percent(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 1)


async def _fetch_trainee_operators(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT
                    id AS operator_id,
                    COALESCE(NULLIF(TRIM(full_name), ''), login) AS operator_name
                FROM users.skystream_users
                WHERE role = 'support'
                  AND is_active IS TRUE
                  AND level = 1
                ORDER BY operator_name
                """
            )
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def _fetch_operator_summaries(
    db: AsyncSession,
    *,
    date_from: date,
    date_to: date,
    today: date,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                f"""
                WITH trainees AS (
                    SELECT
                        id AS operator_id,
                        COALESCE(NULLIF(TRIM(full_name), ''), login) AS operator_name
                    FROM users.skystream_users
                    WHERE role = 'support'
                      AND is_active IS TRUE
                      AND level = 1
                ),
                kb_overall AS (
                    SELECT
                        qa.operator_id,
                        COUNT(*)::int AS attempts_count,
                        COALESCE(
                            AVG(
                                qa.correct_count::float
                                / NULLIF(qa.total_questions, 0)
                                * 100.0
                            ),
                            0
                        ) AS avg_score_percent
                    FROM {_SCHEMA}.kb_quiz_attempts qa
                    WHERE qa.attempt_type = 'kb_topic'
                      AND qa.status = 'finished'
                      {_PRACTICE_FILTER}
                    GROUP BY qa.operator_id
                ),
                articles AS (
                    SELECT
                        t.operator_id,
                        COUNT(DISTINCT a.id)::int AS articles_with_quiz,
                        COUNT(DISTINCT p.article_id) FILTER (
                            WHERE p.quiz_passed_at IS NOT NULL
                        )::int AS articles_passed
                    FROM trainees t
                    CROSS JOIN {_SCHEMA}.kb_articles a
                    JOIN {_SCHEMA}.kb_quizzes q
                        ON q.article_id = a.id AND q.is_active IS TRUE
                    LEFT JOIN {_SCHEMA}.kb_article_progress p
                        ON p.article_id = a.id AND p.operator_id = t.operator_id
                    WHERE a.is_published IS TRUE
                    GROUP BY t.operator_id
                ),
                daily_period AS (
                    SELECT
                        qa.operator_id,
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
                    WHERE qa.attempt_type = 'daily_warmup'
                      AND qa.status = 'finished'
                      AND qa.session_date IS NOT NULL
                      AND qa.session_date >= :date_from
                      AND qa.session_date <= :date_to
                      {_PRACTICE_FILTER}
                    GROUP BY qa.operator_id
                ),
                daily_today AS (
                    SELECT DISTINCT ON (qa.operator_id)
                        qa.operator_id,
                        qa.passed
                    FROM {_SCHEMA}.kb_quiz_attempts qa
                    WHERE qa.attempt_type = 'daily_warmup'
                      AND qa.status = 'finished'
                      AND qa.session_date = :today
                      {_PRACTICE_FILTER}
                    ORDER BY qa.operator_id, qa.finished_at DESC NULLS LAST
                ),
                weak_cat AS (
                    WITH latest_article_attempt AS (
                        SELECT DISTINCT ON (qa.article_id, qa.operator_id)
                            qa.operator_id,
                            a.category_id,
                            qa.correct_count,
                            qa.total_questions
                        FROM {_SCHEMA}.kb_quiz_attempts qa
                        JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                        WHERE qa.attempt_type = 'kb_topic'
                          AND qa.status = 'finished'
                          {_PRACTICE_FILTER}
                        ORDER BY qa.article_id, qa.operator_id, qa.finished_at DESC
                    ),
                    cat_avg AS (
                        SELECT
                            la.operator_id,
                            c.title AS category_title,
                            AVG(
                                la.correct_count::float
                                / NULLIF(la.total_questions, 0)
                                * 100.0
                            ) AS avg_score_percent
                        FROM latest_article_attempt la
                        JOIN {_SCHEMA}.kb_categories c ON c.id = la.category_id
                        GROUP BY la.operator_id, c.id, c.title
                        HAVING COUNT(*) > 0
                    )
                    SELECT DISTINCT ON (operator_id)
                        operator_id,
                        category_title
                    FROM cat_avg
                    ORDER BY operator_id, avg_score_percent ASC NULLS LAST, category_title
                )
                SELECT
                    t.operator_id,
                    t.operator_name,
                    COALESCE(ar.articles_with_quiz, 0) AS kb_articles_with_quiz,
                    COALESCE(ar.articles_passed, 0) AS kb_articles_passed,
                    ROUND(COALESCE(ko.avg_score_percent, 0)::numeric, 1)::float AS kb_avg_score_percent,
                    COALESCE(dp.attempts_count, 0) AS daily_attempts_count,
                    COALESCE(dp.passed_count, 0) AS daily_passed_count,
                    ROUND(COALESCE(dp.avg_score_percent, 0)::numeric, 1)::float AS daily_avg_score_percent,
                    dt.passed AS today_daily_passed,
                    wc.category_title AS weak_category_title
                FROM trainees t
                LEFT JOIN articles ar ON ar.operator_id = t.operator_id
                LEFT JOIN kb_overall ko ON ko.operator_id = t.operator_id
                LEFT JOIN daily_period dp ON dp.operator_id = t.operator_id
                LEFT JOIN daily_today dt ON dt.operator_id = t.operator_id
                LEFT JOIN weak_cat wc ON wc.operator_id = t.operator_id
                ORDER BY t.operator_name
                """
            ),
            {"date_from": date_from, "date_to": date_to, "today": today},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def _needs_attention(row: dict[str, Any]) -> bool:
    kb_total = int(row.get("kb_articles_with_quiz") or 0)
    kb_passed = int(row.get("kb_articles_passed") or 0)
    kb_avg = float(row.get("kb_avg_score_percent") or 0)
    daily_avg = float(row.get("daily_avg_score_percent") or 0)
    daily_attempts = int(row.get("daily_attempts_count") or 0)
    today_passed = row.get("today_daily_passed")

    if kb_total > 0 and kb_passed < kb_total * 0.5:
        return True
    if kb_avg > 0 and kb_avg < 70:
        return True
    if daily_attempts > 0 and daily_avg < 70:
        return True
    if today_passed is False:
        return True
    if row.get("weak_category_title") and kb_avg > 0 and kb_avg < 85:
        return True
    return False


def _team_summary(operators: list[dict[str, Any]]) -> dict[str, Any]:
    if not operators:
        return {
            "operators_count": 0,
            "kb_avg_score_percent": 0.0,
            "articles_passed_ratio_percent": 0.0,
            "daily_avg_score_percent": 0.0,
            "daily_pass_rate_percent": 0.0,
            "needs_attention_count": 0,
        }

    kb_scores = [float(o["kb_avg_score_percent"]) for o in operators if o.get("kb_avg_score_percent")]
    ratios = []
    for o in operators:
        total = int(o.get("kb_articles_with_quiz") or 0)
        passed = int(o.get("kb_articles_passed") or 0)
        if total > 0:
            ratios.append(passed / total * 100)

    daily_scores = [
        float(o["daily_avg_score_percent"])
        for o in operators
        if int(o.get("daily_attempts_count") or 0) > 0
    ]
    daily_passed = sum(int(o.get("daily_passed_count") or 0) for o in operators)
    daily_total = sum(int(o.get("daily_attempts_count") or 0) for o in operators)

    return {
        "operators_count": len(operators),
        "kb_avg_score_percent": round(sum(kb_scores) / len(kb_scores), 1) if kb_scores else 0.0,
        "articles_passed_ratio_percent": round(sum(ratios) / len(ratios), 1) if ratios else 0.0,
        "daily_avg_score_percent": round(sum(daily_scores) / len(daily_scores), 1) if daily_scores else 0.0,
        "daily_pass_rate_percent": round(daily_passed / daily_total * 100, 1) if daily_total else 0.0,
        "needs_attention_count": sum(1 for o in operators if _needs_attention(o)),
    }


async def _fetch_weak_articles(
    db: AsyncSession,
    *,
    operator_id: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                f"""
                WITH latest AS (
                    SELECT DISTINCT ON (qa.article_id)
                        qa.article_id,
                        qa.passed,
                        qa.correct_count,
                        qa.total_questions,
                        a.title AS article_title,
                        a.slug AS article_slug,
                        c.title AS category_title
                    FROM {_SCHEMA}.kb_quiz_attempts qa
                    JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                    LEFT JOIN {_SCHEMA}.kb_categories c ON c.id = a.category_id
                    WHERE qa.operator_id = :operator_id
                      AND qa.attempt_type = 'kb_topic'
                      AND qa.status = 'finished'
                      {_PRACTICE_FILTER}
                    ORDER BY qa.article_id, qa.finished_at DESC NULLS LAST
                )
                SELECT
                    article_id,
                    article_title,
                    article_slug,
                    category_title,
                    passed,
                    correct_count,
                    total_questions
                FROM latest
                WHERE passed IS NOT TRUE
                   OR (
                        correct_count::float
                        / NULLIF(total_questions, 0)
                        * 100.0
                   ) < 100
                ORDER BY
                    passed ASC,
                    correct_count::float / NULLIF(total_questions, 0) ASC NULLS LAST,
                    article_title
                LIMIT :lim
                """
            ),
            {"operator_id": operator_id, "lim": limit},
        )
    ).mappings().all()

    out: list[dict[str, Any]] = []
    for r in rows:
        correct = int(r.get("correct_count") or 0)
        total = int(r.get("total_questions") or 0)
        out.append(
            {
                "article_id": int(r["article_id"]),
                "article_title": str(r.get("article_title") or ""),
                "article_slug": r.get("article_slug"),
                "category_title": r.get("category_title"),
                "passed": bool(r.get("passed")),
                "score_percent": _score_percent(correct, total),
            }
        )
    return out


async def fetch_admin_quiz_training(
    db: AsyncSession,
    *,
    date_from: date,
    date_to: date,
    detail_operator_id: int | None = None,
) -> dict[str, Any]:
    today = date.today()
    operators = await _fetch_operator_summaries(
        db, date_from=date_from, date_to=date_to, today=today
    )
    summary = _team_summary(operators)

    operator_rows = []
    for row in operators:
        operator_rows.append(
            {
                **row,
                "needs_attention": _needs_attention(row),
                "today_daily_label": (
                    "Пройден"
                    if row.get("today_daily_passed") is True
                    else "Не пройден"
                    if row.get("today_daily_passed") is False
                    else "—"
                ),
            }
        )

    detail: dict[str, Any] | None = None
    if detail_operator_id is not None:
        op_row = next(
            (o for o in operator_rows if int(o["operator_id"]) == detail_operator_id),
            None,
        )
        if op_row is None:
            trainees = await _fetch_trainee_operators(db)
            match = next(
                (t for t in trainees if int(t["operator_id"]) == detail_operator_id),
                None,
            )
            if not match:
                return {
                    "summary": summary,
                    "operators": operator_rows,
                    "operator_detail": None,
                }
            op_name = str(match["operator_name"])
        else:
            op_name = str(op_row["operator_name"])

        full = await op_quiz_svc.fetch_operator_quiz_stats(
            db,
            operator_id=detail_operator_id,
            role="support",
            level=1,
        )
        period_daily = (
            {
                "attempts_count": int(op_row.get("daily_attempts_count") or 0),
                "passed_count": int(op_row.get("daily_passed_count") or 0),
                "avg_score_percent": round(
                    float(op_row.get("daily_avg_score_percent") or 0), 1
                ),
            }
            if op_row is not None
            else full.get("daily_overall")
        )
        detail = {
            "operator_id": detail_operator_id,
            "operator_name": op_name,
            **full,
            "daily_overall": period_daily,
            "weak_articles": await _fetch_weak_articles(db, operator_id=detail_operator_id),
        }

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "summary": summary,
        "operators": operator_rows,
        "operator_detail": detail,
    }
