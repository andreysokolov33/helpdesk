"""База знаний операторов — список, поиск, прогресс чтения."""

from __future__ import annotations

import re
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SCHEMA = "helpdesk"

_ARTICLE_ROW_SQL = f"""
SELECT
    c.id AS category_id,
    c.title AS category_title,
    c.slug AS category_slug,
    c.sort_order AS category_sort,
    a.id AS article_id,
    a.slug AS article_slug,
    a.title AS article_title,
    a.subtitle AS article_subtitle,
    a.summary AS article_summary,
    a.sort_order AS article_sort,
    (q.id IS NOT NULL AND q.is_active) AS has_quiz,
    q.id AS quiz_id,
    COALESCE(p.status::text, 'not_started') AS progress_status,
    p.studied_at,
    p.quiz_passed_at,
    la.attempt_status,
    la.passed AS last_attempt_passed,
    la.correct_count,
    la.total_questions
FROM {_SCHEMA}.kb_categories c
JOIN {_SCHEMA}.kb_articles a
    ON a.category_id = c.id AND a.is_published IS TRUE
LEFT JOIN {_SCHEMA}.kb_quizzes q
    ON q.article_id = a.id AND q.is_active IS TRUE
LEFT JOIN {_SCHEMA}.kb_article_progress p
    ON p.article_id = a.id AND p.operator_id = :operator_id
LEFT JOIN LATERAL (
    SELECT
        qa.status::text AS attempt_status,
        qa.passed,
        qa.correct_count,
        qa.total_questions,
        qa.finished_at
    FROM {_SCHEMA}.kb_quiz_attempts qa
    WHERE qa.article_id = a.id
      AND qa.operator_id = :operator_id
    ORDER BY qa.started_at DESC
    LIMIT 1
) la ON TRUE
WHERE c.is_active IS TRUE
"""


def _read_status(row: dict[str, Any]) -> str:
    status = str(row.get("progress_status") or "not_started")
    if row.get("studied_at") or status in {"studied", "completed"}:
        return "read"
    if status == "in_progress":
        return "reading"
    return "unread"


def _quiz_status(row: dict[str, Any]) -> tuple[str, int | None, int | None, int | None]:
    if not row.get("has_quiz"):
        return "none", None, None, None

    progress = str(row.get("progress_status") or "not_started")
    if row.get("quiz_passed_at") or progress == "completed":
        total = row.get("total_questions")
        correct = row.get("correct_count")
        if total is not None and correct is not None:
            return "passed", int(correct), int(total), 0
        return "passed", None, None, None

    attempt_status = row.get("attempt_status")
    if attempt_status == "in_progress":
        return "in_progress", None, None, None

    if attempt_status == "finished":
        total = row.get("total_questions")
        correct = row.get("correct_count")
        passed = bool(row.get("last_attempt_passed"))
        if passed:
            err = 0 if total is None or correct is None else max(int(total) - int(correct), 0)
            return (
                "passed",
                int(correct) if correct is not None else None,
                int(total) if total is not None else None,
                err,
            )
        err = None
        if total is not None and correct is not None:
            err = max(int(total) - int(correct), 0)
        return (
            "failed",
            int(correct) if correct is not None else None,
            int(total) if total is not None else None,
            err,
        )

    return "not_started", None, None, None


def _row_to_list_item(row: dict[str, Any]) -> dict[str, Any]:
    read_status = _read_status(row)
    quiz_status, correct, total, errors = _quiz_status(row)
    attempt_status = row.get("attempt_status")
    quiz_finished_at = row.get("finished_at")
    if attempt_status != "finished":
        quiz_finished_at = None
    return {
        "id": int(row["article_id"]),
        "slug": str(row["article_slug"]),
        "title": str(row["article_title"]),
        "subtitle": row.get("article_subtitle"),
        "summary": row.get("article_summary"),
        "category_id": int(row["category_id"]),
        "category_title": str(row["category_title"]),
        "has_quiz": bool(row.get("has_quiz")),
        "read_status": read_status,
        "quiz_status": quiz_status,
        "quiz_correct_count": correct,
        "quiz_total_questions": total,
        "quiz_error_count": errors,
        "quiz_passed_at": row.get("quiz_passed_at"),
        "quiz_finished_at": quiz_finished_at,
    }


def _group_by_category(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    for row in rows:
        cid = int(row["category_id"])
        if cid not in categories:
            categories[cid] = {
                "id": cid,
                "title": str(row["category_title"]),
                "slug": row.get("category_slug"),
                "sort_order": int(row.get("category_sort") or 0),
                "articles": [],
            }
            order.append(cid)
        categories[cid]["articles"].append(_row_to_list_item(row))
    return [categories[cid] for cid in order]


def _sanitize_search_query(raw: str) -> str:
    q = re.sub(r"\s+", " ", (raw or "").strip())
    return q[:200]


async def fetch_kb_home(db: AsyncSession, *, operator_id: int) -> dict[str, Any]:
    rows = (
        await db.execute(
            text(
                _ARTICLE_ROW_SQL
                + """
                ORDER BY c.sort_order, c.id, a.sort_order, a.id
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().all()

    categories = _group_by_category([dict(r) for r in rows])
    total = sum(len(c["articles"]) for c in categories)
    return {"categories": categories, "total_articles": total}


async def search_kb_articles(
    db: AsyncSession,
    *,
    operator_id: int,
    query: str,
    limit: int = 50,
) -> dict[str, Any]:
    q = _sanitize_search_query(query)
    if len(q) < 2:
        return {"query": q, "items": []}

    like = f"%{q}%"
    ts_query = re.sub(r"[^\w\s\u0400-\u04FF-]+", " ", q, flags=re.UNICODE).strip()
    use_fts = len(ts_query) >= 2

    fts_clause = """
                  AND (
                        a.search_vector @@ plainto_tsquery('russian', :ts_q)
                     OR a.title ILIKE :like
                     OR COALESCE(a.summary, '') ILIKE :like
                     OR a.content_html ILIKE :like
                  )
    """ if use_fts else """
                  AND (
                        a.title ILIKE :like
                     OR COALESCE(a.summary, '') ILIKE :like
                     OR a.content_html ILIKE :like
                  )
    """
    order_clause = """
                ORDER BY
                    ts_rank(a.search_vector, plainto_tsquery('russian', :ts_q)) DESC NULLS LAST,
                    a.title
    """ if use_fts else """
                ORDER BY a.title
    """

    params: dict[str, Any] = {
        "operator_id": operator_id,
        "like": like,
        "limit": limit,
    }
    if use_fts:
        params["ts_q"] = ts_query

    rows = (
        await db.execute(
            text(
                _ARTICLE_ROW_SQL
                + fts_clause
                + order_clause
                + """
                LIMIT :limit
                """
            ),
            params,
        )
    ).mappings().all()

    return {"query": q, "items": [_row_to_list_item(dict(r)) for r in rows]}


async def fetch_kb_article_detail(
    db: AsyncSession,
    *,
    operator_id: int,
    slug: str,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                _ARTICLE_ROW_SQL
                + """
                  AND a.slug = :slug
                LIMIT 1
                """
            ),
            {"operator_id": operator_id, "slug": slug},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    content = (
        await db.execute(
            text(
                f"""
                SELECT content_html, sidebar_json, published_at
                FROM {_SCHEMA}.kb_articles
                WHERE id = :article_id AND is_published IS TRUE
                """
            ),
            {"article_id": int(row["article_id"])},
        )
    ).mappings().first()
    if not content:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    item = _row_to_list_item(dict(row))
    return {
        **item,
        "content_html": str(content["content_html"] or ""),
        "sidebar_json": content.get("sidebar_json") or {},
        "quiz_id": int(row["quiz_id"]) if row.get("quiz_id") else None,
        "published_at": content.get("published_at"),
    }


async def touch_kb_article_view(
    db: AsyncSession,
    *,
    operator_id: int,
    article_id: int,
) -> None:
    await db.execute(
        text(
            f"""
            INSERT INTO {_SCHEMA}.kb_article_progress (
                operator_id, article_id, status, content_version
            )
            SELECT
                :operator_id,
                a.id,
                'in_progress'::helpdesk.kb_progress_status,
                a.version
            FROM {_SCHEMA}.kb_articles a
            WHERE a.id = :article_id AND a.is_published IS TRUE
            ON CONFLICT (operator_id, article_id) DO UPDATE SET
                status = CASE
                    WHEN {_SCHEMA}.kb_article_progress.status IN (
                        'studied', 'completed'
                    ) THEN {_SCHEMA}.kb_article_progress.status
                    ELSE 'in_progress'::helpdesk.kb_progress_status
                END,
                updated_at = NOW()
            """
        ),
        {"operator_id": operator_id, "article_id": article_id},
    )
    await db.commit()


async def mark_kb_article_studied(
    db: AsyncSession,
    *,
    operator_id: int,
    article_id: int,
) -> dict[str, Any]:
    exists = (
        await db.execute(
            text(
                f"""
                SELECT id FROM {_SCHEMA}.kb_articles
                WHERE id = :article_id AND is_published IS TRUE
                """
            ),
            {"article_id": article_id},
        )
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    row = (
        await db.execute(
            text(
                f"""
                INSERT INTO {_SCHEMA}.kb_article_progress (
                    operator_id, article_id, status, studied_at, content_version
                )
                SELECT
                    :operator_id,
                    a.id,
                    CASE
                        WHEN a.quiz_required IS FALSE THEN 'completed'::helpdesk.kb_progress_status
                        ELSE 'studied'::helpdesk.kb_progress_status
                    END,
                    NOW(),
                    a.version
                FROM {_SCHEMA}.kb_articles a
                WHERE a.id = :article_id
                ON CONFLICT (operator_id, article_id) DO UPDATE SET
                    status = CASE
                        WHEN {_SCHEMA}.kb_article_progress.status = 'completed'
                            THEN 'completed'::helpdesk.kb_progress_status
                        WHEN EXCLUDED.status = 'completed'::helpdesk.kb_progress_status
                            THEN 'completed'::helpdesk.kb_progress_status
                        ELSE 'studied'::helpdesk.kb_progress_status
                    END,
                    studied_at = COALESCE(
                        {_SCHEMA}.kb_article_progress.studied_at,
                        NOW()
                    ),
                    content_version = EXCLUDED.content_version,
                    updated_at = NOW()
                RETURNING studied_at, status::text AS status
                """
            ),
            {"operator_id": operator_id, "article_id": article_id},
        )
    ).mappings().first()
    await db.commit()

    status = str(row["status"]) if row else "studied"
    read_status = "read" if status in {"studied", "completed"} else "reading"
    return {
        "article_id": article_id,
        "read_status": read_status,
        "studied_at": row.get("studied_at") if row else None,
    }


async def _load_quiz_questions(db: AsyncSession, quiz_id: int) -> list[dict[str, Any]]:
    q_rows = (
        await db.execute(
            text(
                f"""
                SELECT id, question_text, selection_mode::text, sort_order
                FROM {_SCHEMA}.kb_questions
                WHERE quiz_id = :quiz_id AND is_active IS TRUE
                ORDER BY sort_order, id
                """
            ),
            {"quiz_id": quiz_id},
        )
    ).mappings().all()
    if not q_rows:
        return []

    q_ids = [int(r["id"]) for r in q_rows]
    opt_rows = (
        await db.execute(
            text(
                f"""
                SELECT id, question_id, option_text, sort_order
                FROM {_SCHEMA}.kb_question_options
                WHERE question_id = ANY(:q_ids)
                ORDER BY question_id, sort_order, id
                """
            ),
            {"q_ids": q_ids},
        )
    ).mappings().all()
    opts_by_q: dict[int, list[dict[str, Any]]] = {}
    for opt in opt_rows:
        qid = int(opt["question_id"])
        opts_by_q.setdefault(qid, []).append(
            {
                "id": int(opt["id"]),
                "option_text": str(opt["option_text"]),
                "sort_order": int(opt["sort_order"]),
            }
        )

    return [
        {
            "id": int(q["id"]),
            "question_text": str(q["question_text"]),
            "selection_mode": str(q["selection_mode"]),
            "sort_order": int(q["sort_order"]),
            "options": opts_by_q.get(int(q["id"]), []),
        }
        for q in q_rows
    ]


async def fetch_kb_quiz_session(
    db: AsyncSession,
    *,
    operator_id: int,
    slug: str,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    a.id AS article_id,
                    q.id AS quiz_id,
                    q.title AS quiz_title,
                    q.passing_score_percent
                FROM {_SCHEMA}.kb_articles a
                JOIN {_SCHEMA}.kb_quizzes q
                    ON q.article_id = a.id AND q.is_active IS TRUE
                WHERE a.slug = :slug AND a.is_published IS TRUE
                """
            ),
            {"slug": slug},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Тест для статьи не найден")

    quiz_id = int(row["quiz_id"])
    questions = await _load_quiz_questions(db, quiz_id)

    attempt = (
        await db.execute(
            text(
                f"""
                SELECT id, status::text, passed, score, total_questions, correct_count
                FROM {_SCHEMA}.kb_quiz_attempts
                WHERE quiz_id = :quiz_id
                  AND operator_id = :operator_id
                  AND attempt_type = 'kb_topic'
                ORDER BY started_at DESC
                LIMIT 1
                """
            ),
            {"quiz_id": quiz_id, "operator_id": operator_id},
        )
    ).mappings().first()

    answered: list[dict[str, Any]] = []
    attempt_id: int | None = None
    attempt_status = "none"
    passed: bool | None = None
    score: int | None = None
    total_questions = len(questions)
    correct_count: int | None = None

    if attempt:
        attempt_id = int(attempt["id"])
        attempt_status = str(attempt["status"])
        if attempt_status == "finished":
            passed = bool(attempt["passed"])
            score = int(attempt["score"])
            total_questions = int(attempt["total_questions"])
            correct_count = int(attempt["correct_count"])
        elif attempt_status == "in_progress":
            ans_rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT question_id, selected_option_ids, is_correct
                        FROM {_SCHEMA}.kb_quiz_attempt_answers
                        WHERE attempt_id = :attempt_id
                        ORDER BY answered_at, id
                        """
                    ),
                    {"attempt_id": attempt_id},
                )
            ).mappings().all()
            answered = [
                {
                    "question_id": int(a["question_id"]),
                    "selected_option_ids": list(a["selected_option_ids"] or []),
                    "is_correct": bool(a["is_correct"]),
                }
                for a in ans_rows
            ]

    return {
        "quiz_id": quiz_id,
        "article_id": int(row["article_id"]),
        "title": str(row["quiz_title"]),
        "passing_score_percent": int(row["passing_score_percent"]),
        "attempt_id": attempt_id,
        "attempt_status": attempt_status,
        "passed": passed,
        "score": score,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "questions": questions,
        "answered": answered,
    }


async def start_kb_quiz_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    slug: str,
) -> dict[str, Any]:
    session = await fetch_kb_quiz_session(db, operator_id=operator_id, slug=slug)
    if session["attempt_status"] == "in_progress" and session["attempt_id"]:
        return {
            "attempt_id": session["attempt_id"],
            "total_questions": session["total_questions"],
        }

    if session["attempt_status"] == "finished" and session.get("passed"):
        raise HTTPException(status_code=409, detail="Тест уже успешно сдан")

    questions = session["questions"]
    if not questions:
        raise HTTPException(status_code=400, detail="В тесте нет вопросов")

    article_id = int(session["article_id"])
    quiz_id = int(session["quiz_id"])
    version = (
        await db.execute(
            text(f"SELECT version FROM {_SCHEMA}.kb_articles WHERE id = :id"),
            {"id": article_id},
        )
    ).scalar_one()

    attempt_id = (
        await db.execute(
            text(
                f"""
                INSERT INTO {_SCHEMA}.kb_quiz_attempts (
                    operator_id, quiz_id, article_id, attempt_type, status,
                    total_questions, content_version
                ) VALUES (
                    :operator_id, :quiz_id, :article_id,
                    'kb_topic'::helpdesk.kb_quiz_attempt_type,
                    'in_progress'::helpdesk.kb_quiz_attempt_status,
                    :total_questions, :version
                )
                RETURNING id
                """
            ),
            {
                "operator_id": operator_id,
                "quiz_id": quiz_id,
                "article_id": article_id,
                "total_questions": len(questions),
                "version": int(version),
            },
        )
    ).scalar_one()

    await db.execute(
        text(
            f"""
            INSERT INTO {_SCHEMA}.kb_article_progress (
                operator_id, article_id, status, last_attempt_id, content_version
            )
            SELECT
                :operator_id, :article_id,
                'in_progress'::helpdesk.kb_progress_status,
                :attempt_id, :version
            FROM {_SCHEMA}.kb_articles a
            WHERE a.id = :article_id
            ON CONFLICT (operator_id, article_id) DO UPDATE SET
                last_attempt_id = EXCLUDED.last_attempt_id,
                status = CASE
                    WHEN {_SCHEMA}.kb_article_progress.status = 'completed'
                        THEN 'completed'::helpdesk.kb_progress_status
                    ELSE 'in_progress'::helpdesk.kb_progress_status
                END,
                updated_at = NOW()
            """
        ),
        {
            "operator_id": operator_id,
            "article_id": article_id,
            "attempt_id": int(attempt_id),
            "version": int(version),
        },
    )
    await db.commit()
    return {"attempt_id": int(attempt_id), "total_questions": len(questions)}


async def submit_kb_quiz_answer(
    db: AsyncSession,
    *,
    operator_id: int,
    attempt_id: int,
    question_id: int,
    selected_option_ids: list[int],
) -> dict[str, Any]:
    attempt = (
        await db.execute(
            text(
                f"""
                SELECT id, quiz_id, status::text
                FROM {_SCHEMA}.kb_quiz_attempts
                WHERE id = :attempt_id
                  AND operator_id = :operator_id
                """
            ),
            {"attempt_id": attempt_id, "operator_id": operator_id},
        )
    ).mappings().first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    if str(attempt["status"]) != "in_progress":
        raise HTTPException(status_code=409, detail="Попытка уже завершена")

    exists = (
        await db.execute(
            text(
                f"""
                SELECT 1 FROM {_SCHEMA}.kb_quiz_attempt_answers
                WHERE attempt_id = :attempt_id AND question_id = :question_id
                """
            ),
            {"attempt_id": attempt_id, "question_id": question_id},
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="На этот вопрос уже дан ответ")

    question = (
        await db.execute(
            text(
                f"""
                SELECT id, explanation
                FROM {_SCHEMA}.kb_questions
                WHERE id = :question_id AND quiz_id = :quiz_id AND is_active IS TRUE
                """
            ),
            {"question_id": question_id, "quiz_id": int(attempt["quiz_id"])},
        )
    ).mappings().first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    correct_rows = (
        await db.execute(
            text(
                f"""
                SELECT id FROM {_SCHEMA}.kb_question_options
                WHERE question_id = :question_id AND is_correct IS TRUE
                """
            ),
            {"question_id": question_id},
        )
    ).scalars().all()
    correct_ids = {int(x) for x in correct_rows}
    selected = {int(x) for x in selected_option_ids}
    is_correct = bool(selected) and selected == correct_ids

    await db.execute(
        text(
            f"""
            INSERT INTO {_SCHEMA}.kb_quiz_attempt_answers (
                attempt_id, question_id, selected_option_ids, is_correct
            ) VALUES (
                :attempt_id, :question_id, :selected_option_ids, :is_correct
            )
            """
        ),
        {
            "attempt_id": attempt_id,
            "question_id": question_id,
            "selected_option_ids": list(selected),
            "is_correct": is_correct,
        },
    )
    await db.commit()
    return {
        "is_correct": is_correct,
        "explanation": question.get("explanation"),
        "correct_option_ids": sorted(correct_ids),
    }


async def finish_kb_quiz_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    attempt_id: int,
) -> dict[str, Any]:
    attempt = (
        await db.execute(
            text(
                f"""
                SELECT
                    qa.id,
                    qa.article_id,
                    qa.quiz_id,
                    qa.status::text AS status,
                    qa.total_questions,
                    q.passing_score_percent,
                    a.pass_score_percent AS article_pass_score_percent,
                    a.quiz_required
                FROM {_SCHEMA}.kb_quiz_attempts qa
                JOIN {_SCHEMA}.kb_quizzes q ON q.id = qa.quiz_id
                JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                WHERE qa.id = :attempt_id AND qa.operator_id = :operator_id
                """
            ),
            {"attempt_id": attempt_id, "operator_id": operator_id},
        )
    ).mappings().first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    if str(attempt["status"]) != "in_progress":
        raise HTTPException(status_code=409, detail="Попытка уже завершена")

    stats = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(*)::int AS answered_count,
                    COUNT(*) FILTER (WHERE is_correct)::int AS correct_count
                FROM {_SCHEMA}.kb_quiz_attempt_answers
                WHERE attempt_id = :attempt_id
                """
            ),
            {"attempt_id": attempt_id},
        )
    ).mappings().one()

    total = int(attempt["total_questions"])
    correct = int(stats["correct_count"] or 0)
    threshold = int(attempt["passing_score_percent"] or attempt["article_pass_score_percent"] or 100)
    percent = int(round((correct / total) * 100)) if total else 0
    passed = percent >= threshold

    await db.execute(
        text(
            f"""
            UPDATE {_SCHEMA}.kb_quiz_attempts
            SET
                status = 'finished'::helpdesk.kb_quiz_attempt_status,
                score = :correct,
                correct_count = :correct,
                passed = :passed,
                finished_at = NOW()
            WHERE id = :attempt_id
            """
        ),
        {"attempt_id": attempt_id, "correct": correct, "passed": passed},
    )

    if passed:
        await db.execute(
            text(
                f"""
                INSERT INTO {_SCHEMA}.kb_article_progress (
                    operator_id, article_id, status, studied_at,
                    quiz_passed_at, last_attempt_id, content_version
                )
                SELECT
                    :operator_id, a.id,
                    'completed'::helpdesk.kb_progress_status,
                    COALESCE(p.studied_at, NOW()),
                    NOW(),
                    :attempt_id,
                    a.version
                FROM {_SCHEMA}.kb_articles a
                LEFT JOIN {_SCHEMA}.kb_article_progress p
                    ON p.article_id = a.id AND p.operator_id = :operator_id
                WHERE a.id = :article_id
                ON CONFLICT (operator_id, article_id) DO UPDATE SET
                    status = 'completed'::helpdesk.kb_progress_status,
                    studied_at = COALESCE(
                        {_SCHEMA}.kb_article_progress.studied_at, NOW()
                    ),
                    quiz_passed_at = NOW(),
                    last_attempt_id = EXCLUDED.last_attempt_id,
                    updated_at = NOW()
                """
            ),
            {
                "operator_id": operator_id,
                "article_id": int(attempt["article_id"]),
                "attempt_id": attempt_id,
            },
        )
    else:
        await db.execute(
            text(
                f"""
                UPDATE {_SCHEMA}.kb_article_progress
                SET last_attempt_id = :attempt_id, updated_at = NOW()
                WHERE operator_id = :operator_id AND article_id = :article_id
                """
            ),
            {
                "operator_id": operator_id,
                "article_id": int(attempt["article_id"]),
                "attempt_id": attempt_id,
            },
        )

    await db.commit()

    timestamps = (
        await db.execute(
            text(
                f"""
                SELECT
                    p.quiz_passed_at,
                    qa.finished_at AS quiz_finished_at
                FROM {_SCHEMA}.kb_quiz_attempts qa
                LEFT JOIN {_SCHEMA}.kb_article_progress p
                    ON p.article_id = qa.article_id
                   AND p.operator_id = qa.operator_id
                WHERE qa.id = :attempt_id
                """
            ),
            {"attempt_id": attempt_id},
        )
    ).mappings().one()

    quiz_status = "passed" if passed else "failed"
    read_status = "read" if passed else "reading"
    return {
        "attempt_id": attempt_id,
        "passed": passed,
        "score": correct,
        "total_questions": total,
        "correct_count": correct,
        "error_count": max(total - correct, 0),
        "quiz_status": quiz_status,
        "read_status": read_status,
        "quiz_passed_at": timestamps.get("quiz_passed_at"),
        "quiz_finished_at": timestamps.get("quiz_finished_at"),
    }
