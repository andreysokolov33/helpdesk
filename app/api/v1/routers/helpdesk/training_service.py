"""Тренажёр (/train): бесконечные тренировочные сессии по вопросам базы знаний.

Таблицы: helpdesk.kb_training_sessions, helpdesk.kb_training_answers
(sql/migrations/20261008_helpdesk_kb_training.sql). kb_quiz_attempts и статистику
тестов не трогаем.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth.dao import SkystreamUsersDAO
from app.api.v1.routers.helpdesk import admin_quiz_stats_service as admin_quiz_svc
from app.api.v1.routers.helpdesk import stats_service as stats_svc
from app.api.v1.routers.helpdesk.daily_quiz_service import _load_active_policy
from app.api.v1.routers.helpdesk.manager_contacts_service import (
    apply_contacts_to_quiz_questions,
    load_manager_contact_lists,
    substitute_manager_contacts,
)
from app.api.v1.routers.helpdesk.training_leaderboard import build_leaderboard, raw_percent

_SCHEMA = "helpdesk"

# Через сколько минут без ответов активная сессия автоматически становится abandoned.
TRAINING_INACTIVITY_MINUTES = 30
# Часовой пояс для фильтра «от и до» по answered_at (как у политики ежедневного теста).
TRAINING_TIMEZONE = "Europe/Moscow"
LEADERS_LIMIT = 10

DAILY_SOURCE_TITLE = "Ежедневные вопросы"
# Сессия «все тесты статей»: article_id и category_id пусты, источник узнаём по названию.
ALL_ARTICLES_TITLE = "Все тесты статей"

_SESSION_COLUMNS = f"""
    s.id,
    s.operator_id,
    s.source_type::text AS source_type,
    s.source_title,
    s.quiz_id,
    s.article_id,
    s.category_id,
    s.policy_id,
    s.status::text AS status,
    s.question_queue,
    s.current_question_id,
    s.round_no,
    s.started_at,
    s.last_answer_at,
    s.finished_at,
    s.total_answers,
    s.correct_count
"""

# Вопрос пригоден для тренажёра: активен, в активном квизе и имеет хотя бы один верный вариант.
_POOL_BASE_SQL = f"""
SELECT q.id
FROM {_SCHEMA}.kb_questions q
JOIN {_SCHEMA}.kb_quizzes qz ON qz.id = q.quiz_id AND qz.is_active IS TRUE
JOIN {_SCHEMA}.kb_articles a ON a.id = qz.article_id
WHERE q.is_active IS TRUE
  AND EXISTS (
        SELECT 1 FROM {_SCHEMA}.kb_question_options o
        WHERE o.question_id = q.id AND o.is_correct IS TRUE
  )
"""


# ---------------------------------------------------------------------------
# Общие помощники
# ---------------------------------------------------------------------------


def period_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    """[начало date_from; начало date_to + 1 день) в часовом поясе тренажёра."""
    tz = ZoneInfo(TRAINING_TIMEZONE)
    start = datetime.combine(date_from, time.min, tzinfo=tz)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=tz)
    return start, end


def _duration_sec(started_at: datetime | None, last_answer_at: datetime | None) -> int:
    if not started_at or not last_answer_at:
        return 0
    return max(int((last_answer_at - started_at).total_seconds()), 0)


def _source_kind_label(row: dict[str, Any]) -> str:
    if row.get("source_type") == "daily":
        return "Пул ежедневного теста"
    if row.get("category_id") is not None and row.get("article_id") is None:
        return "Раздел"
    if row.get("article_id") is None and row.get("source_title") == ALL_ARTICLES_TITLE:
        return "Все статьи"
    return "Статья"


def _session_state(row: dict[str, Any]) -> dict[str, Any]:
    total = int(row.get("total_answers") or 0)
    correct = int(row.get("correct_count") or 0)
    return {
        "id": int(row["id"]),
        "source_type": str(row["source_type"]),
        "source_title": str(row.get("source_title") or ""),
        "source_kind_label": _source_kind_label(row),
        "article_id": int(row["article_id"]) if row.get("article_id") is not None else None,
        "category_id": int(row["category_id"]) if row.get("category_id") is not None else None,
        "status": str(row["status"]),
        "started_at": row["started_at"],
        "last_answer_at": row.get("last_answer_at"),
        "finished_at": row.get("finished_at"),
        "total_answers": total,
        "correct_count": correct,
        "wrong_count": max(total - correct, 0),
        "score_percent": raw_percent(correct, total),
        "duration_sec": _duration_sec(row.get("started_at"), row.get("last_answer_at")),
        "inactivity_minutes": TRAINING_INACTIVITY_MINUTES,
    }


def _session_list_item(row: dict[str, Any]) -> dict[str, Any]:
    state = _session_state(row)
    state.pop("article_id", None)
    state.pop("category_id", None)
    state.pop("inactivity_minutes", None)
    return state


async def expire_stale_sessions(db: AsyncSession, *, operator_id: int | None = None) -> None:
    """Авто-abandoned: нет ответов дольше TRAINING_INACTIVITY_MINUTES (без коммита)."""
    params: dict[str, Any] = {"mins": TRAINING_INACTIVITY_MINUTES}
    operator_filter = ""
    if operator_id is not None:
        operator_filter = "AND operator_id = :operator_id"
        params["operator_id"] = operator_id
    await db.execute(
        text(
            f"""
            UPDATE {_SCHEMA}.kb_training_sessions
            SET
                status = 'abandoned'::helpdesk.kb_training_session_status,
                finished_at = COALESCE(last_answer_at, started_at),
                current_question_id = NULL
            WHERE status = 'in_progress'
              AND COALESCE(last_answer_at, started_at) < NOW() - make_interval(mins => :mins)
              {operator_filter}
            """
        ),
        params,
    )


async def _load_session(
    db: AsyncSession,
    *,
    operator_id: int,
    session_id: int,
    for_update: bool = False,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                f"""
                SELECT {_SESSION_COLUMNS}
                FROM {_SCHEMA}.kb_training_sessions s
                WHERE s.id = :session_id AND s.operator_id = :operator_id
                {"FOR UPDATE" if for_update else ""}
                """
            ),
            {"session_id": session_id, "operator_id": operator_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Сессия тренажёра не найдена")
    return dict(row)


async def _pool_question_ids(db: AsyncSession, session: dict[str, Any]) -> list[int]:
    if session["source_type"] == "daily":
        if session.get("quiz_id") is None:
            return []
        where = "AND qz.id = :quiz_id"
        params: dict[str, Any] = {"quiz_id": int(session["quiz_id"])}
    elif session.get("article_id") is not None:
        where = "AND a.id = :article_id AND a.is_published IS TRUE"
        params = {"article_id": int(session["article_id"])}
    elif session.get("category_id") is not None:
        where = "AND a.category_id = :category_id AND a.is_published IS TRUE"
        params = {"category_id": int(session["category_id"])}
    elif session.get("source_title") == ALL_ARTICLES_TITLE:
        where = "AND a.is_published IS TRUE"
        params = {}
    else:
        return []

    rows = (
        await db.execute(text(_POOL_BASE_SQL + where + " ORDER BY q.id"), params)
    ).scalars().all()
    return [int(x) for x in rows]


async def _load_public_question(db: AsyncSession, question_id: int) -> dict[str, Any] | None:
    q = (
        await db.execute(
            text(
                f"""
                SELECT id, question_text, selection_mode::text AS selection_mode, sort_order
                FROM {_SCHEMA}.kb_questions
                WHERE id = :question_id
                """
            ),
            {"question_id": question_id},
        )
    ).mappings().first()
    if not q:
        return None
    options = (
        await db.execute(
            text(
                f"""
                SELECT id, option_text, sort_order
                FROM {_SCHEMA}.kb_question_options
                WHERE question_id = :question_id
                ORDER BY sort_order, id
                """
            ),
            {"question_id": question_id},
        )
    ).mappings().all()
    question = {
        "id": int(q["id"]),
        "question_text": str(q["question_text"]),
        "selection_mode": str(q["selection_mode"]),
        "sort_order": int(q["sort_order"]),
        "options": [
            {
                "id": int(o["id"]),
                "option_text": str(o["option_text"]),
                "sort_order": int(o["sort_order"]),
            }
            for o in options
        ],
    }
    phones, emails = await load_manager_contact_lists(db)
    return apply_contacts_to_quiz_questions([question], phones=phones, emails=emails)[0]


def _shuffled_round(pool: list[int], *, avoid_first: int | None) -> list[int]:
    """Новый круг: случайный порядок, по возможности не начинаем с только что отвеченного вопроса."""
    queue = list(pool)
    random.shuffle(queue)
    if avoid_first is not None and len(queue) > 1 and queue[0] == avoid_first:
        swap = random.randrange(1, len(queue))
        queue[0], queue[swap] = queue[swap], queue[0]
    return queue


# ---------------------------------------------------------------------------
# Источники
# ---------------------------------------------------------------------------


async def fetch_training_sources(db: AsyncSession) -> dict[str, Any]:
    policy = await _load_active_policy(db)
    daily_count = 0
    if policy:
        daily_count = int(
            (
                await db.execute(
                    text(f"SELECT COUNT(*) FROM ({_POOL_BASE_SQL} AND qz.id = :quiz_id) pool"),
                    {"quiz_id": int(policy["quiz_id"])},
                )
            ).scalar_one()
        )

    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    c.id AS category_id,
                    c.title AS category_title,
                    a.id AS article_id,
                    a.slug AS article_slug,
                    a.title AS article_title,
                    COUNT(q.id)::int AS questions_count
                FROM {_SCHEMA}.kb_categories c
                JOIN {_SCHEMA}.kb_articles a
                    ON a.category_id = c.id AND a.is_published IS TRUE
                JOIN {_SCHEMA}.kb_quizzes qz
                    ON qz.article_id = a.id AND qz.is_active IS TRUE
                JOIN {_SCHEMA}.kb_questions q
                    ON q.quiz_id = qz.id AND q.is_active IS TRUE
                WHERE c.is_active IS TRUE
                  AND EXISTS (
                        SELECT 1 FROM {_SCHEMA}.kb_question_options o
                        WHERE o.question_id = q.id AND o.is_correct IS TRUE
                  )
                GROUP BY c.id, c.title, c.sort_order, a.id, a.slug, a.title, a.sort_order
                ORDER BY c.sort_order, c.id, a.sort_order, a.id
                """
            )
        )
    ).mappings().all()

    categories: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    for r in rows:
        cid = int(r["category_id"])
        if cid not in categories:
            categories[cid] = {
                "id": cid,
                "title": str(r["category_title"]),
                "questions_count": 0,
                "articles": [],
            }
            order.append(cid)
        count = int(r["questions_count"] or 0)
        categories[cid]["questions_count"] += count
        categories[cid]["articles"].append(
            {
                "id": int(r["article_id"]),
                "slug": str(r["article_slug"]),
                "title": str(r["article_title"]),
                "questions_count": count,
            }
        )

    return {
        "daily": {
            "available": bool(policy) and daily_count > 0,
            "title": DAILY_SOURCE_TITLE,
            "questions_count": daily_count,
        },
        "all_articles": {
            "questions_count": sum(c["questions_count"] for c in categories.values()),
            "articles_count": sum(len(c["articles"]) for c in categories.values()),
        },
        "categories": [categories[cid] for cid in order],
        "inactivity_minutes": TRAINING_INACTIVITY_MINUTES,
    }


# ---------------------------------------------------------------------------
# Сессия оператора
# ---------------------------------------------------------------------------


async def _resolve_source(
    db: AsyncSession,
    *,
    source_type: str,
    article_id: int | None,
    category_id: int | None,
    all_articles: bool = False,
) -> dict[str, Any]:
    if source_type == "daily":
        policy = await _load_active_policy(db)
        if not policy:
            raise HTTPException(status_code=404, detail="Ежедневные вопросы не настроены")
        return {
            "source_type": "daily",
            "quiz_id": int(policy["quiz_id"]),
            "article_id": None,
            "category_id": None,
            "policy_id": int(policy["id"]),
            "source_title": DAILY_SOURCE_TITLE,
        }

    if all_articles:
        return {
            "source_type": "article",
            "quiz_id": None,
            "article_id": None,
            "category_id": None,
            "policy_id": None,
            "source_title": ALL_ARTICLES_TITLE,
        }

    if article_id is not None:
        row = (
            await db.execute(
                text(
                    f"""
                    SELECT a.id, a.title, a.category_id, qz.id AS quiz_id
                    FROM {_SCHEMA}.kb_articles a
                    JOIN {_SCHEMA}.kb_quizzes qz
                        ON qz.article_id = a.id AND qz.is_active IS TRUE
                    WHERE a.id = :article_id AND a.is_published IS TRUE
                    """
                ),
                {"article_id": article_id},
            )
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Тест статьи не найден")
        return {
            "source_type": "article",
            "quiz_id": int(row["quiz_id"]),
            "article_id": int(row["id"]),
            "category_id": int(row["category_id"]),
            "policy_id": None,
            "source_title": str(row["title"]),
        }

    row = (
        await db.execute(
            text(
                f"""
                SELECT id, title
                FROM {_SCHEMA}.kb_categories
                WHERE id = :category_id AND is_active IS TRUE
                """
            ),
            {"category_id": category_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Раздел не найден")
    return {
        "source_type": "article",
        "quiz_id": None,
        "article_id": None,
        "category_id": int(row["id"]),
        "policy_id": None,
        "source_title": str(row["title"]),
    }


async def start_training_session(
    db: AsyncSession,
    *,
    operator_id: int,
    source_type: str,
    article_id: int | None,
    category_id: int | None,
    all_articles: bool = False,
) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)

    source = await _resolve_source(
        db,
        source_type=source_type,
        article_id=article_id,
        category_id=category_id,
        all_articles=all_articles,
    )
    pool = await _pool_question_ids(db, source)
    if not pool:
        raise HTTPException(status_code=400, detail="В выбранном источнике нет вопросов")

    # Одна активная сессия на оператора: предыдущую закрываем.
    await db.execute(
        text(
            f"""
            UPDATE {_SCHEMA}.kb_training_sessions
            SET
                status = CASE
                    WHEN total_answers > 0 THEN 'finished'::helpdesk.kb_training_session_status
                    ELSE 'abandoned'::helpdesk.kb_training_session_status
                END,
                finished_at = NOW(),
                current_question_id = NULL
            WHERE operator_id = :operator_id AND status = 'in_progress'
            """
        ),
        {"operator_id": operator_id},
    )

    row = (
        await db.execute(
            text(
                f"""
                INSERT INTO {_SCHEMA}.kb_training_sessions AS s (
                    operator_id, source_type, quiz_id, article_id, category_id, policy_id,
                    source_title, question_queue, round_no
                ) VALUES (
                    :operator_id,
                    CAST(:source_type AS helpdesk.kb_training_source_type),
                    :quiz_id, :article_id, :category_id, :policy_id,
                    :source_title, CAST(:queue AS bigint[]), 1
                )
                RETURNING {_SESSION_COLUMNS}
                """
            ),
            {
                "operator_id": operator_id,
                "source_type": source["source_type"],
                "quiz_id": source["quiz_id"],
                "article_id": source["article_id"],
                "category_id": source["category_id"],
                "policy_id": source["policy_id"],
                "source_title": source["source_title"],
                "queue": _shuffled_round(pool, avoid_first=None),
            },
        )
    ).mappings().one()
    await db.commit()
    return _session_state(dict(row))


async def fetch_active_session(db: AsyncSession, *, operator_id: int) -> dict[str, Any] | None:
    await expire_stale_sessions(db, operator_id=operator_id)
    row = (
        await db.execute(
            text(
                f"""
                SELECT {_SESSION_COLUMNS}
                FROM {_SCHEMA}.kb_training_sessions s
                WHERE s.operator_id = :operator_id AND s.status = 'in_progress'
                ORDER BY s.started_at DESC
                LIMIT 1
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().first()
    await db.commit()
    return _session_state(dict(row)) if row else None


async def fetch_session(db: AsyncSession, *, operator_id: int, session_id: int) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)
    session = await _load_session(db, operator_id=operator_id, session_id=session_id)
    await db.commit()
    return _session_state(session)


async def next_training_question(
    db: AsyncSession,
    *,
    operator_id: int,
    session_id: int,
) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)
    session = await _load_session(
        db, operator_id=operator_id, session_id=session_id, for_update=True
    )
    if session["status"] != "in_progress":
        await db.commit()
        return {"session": _session_state(session), "question": None}

    pool = await _pool_question_ids(db, session)
    pool_set = set(pool)
    queue = [int(x) for x in (session.get("question_queue") or []) if int(x) in pool_set]
    round_no = int(session.get("round_no") or 0)
    current = session.get("current_question_id")
    current = int(current) if current is not None and int(current) in pool_set else None

    if current is None and pool:
        if not queue:
            last_answered = (
                await db.execute(
                    text(
                        f"""
                        SELECT question_id FROM {_SCHEMA}.kb_training_answers
                        WHERE session_id = :session_id
                        ORDER BY answered_at DESC, id DESC
                        LIMIT 1
                        """
                    ),
                    {"session_id": session_id},
                )
            ).scalar_one_or_none()
            queue = _shuffled_round(pool, avoid_first=last_answered)
            round_no += 1
        current = queue.pop(0)

    await db.execute(
        text(
            f"""
            UPDATE {_SCHEMA}.kb_training_sessions
            SET current_question_id = :current,
                question_queue = CAST(:queue AS bigint[]),
                round_no = :round_no
            WHERE id = :session_id
            """
        ),
        {"current": current, "queue": queue, "round_no": round_no, "session_id": session_id},
    )
    await db.commit()

    question = await _load_public_question(db, current) if current is not None else None
    return {
        "session": _session_state(session),
        "question": question,
        "round_no": round_no,
        "round_position": len(pool) - len(queue) if current is not None else 0,
        "pool_size": len(pool),
    }


async def _resolve_answer_article(db: AsyncSession, question_id: int) -> dict[str, Any] | None:
    """Статья вопроса: question → quiz → article (если опубликована),
    иначе (пул ежедневного теста в служебной статье) — опубликованная статья по тегу-slug."""
    row = (
        await db.execute(
            text(
                f"""
                SELECT a.id, a.slug, a.title
                FROM {_SCHEMA}.kb_questions q
                JOIN {_SCHEMA}.kb_quizzes qz ON qz.id = q.quiz_id
                JOIN LATERAL (
                    SELECT a1.id, a1.slug, a1.title, 0 AS prio
                    FROM {_SCHEMA}.kb_articles a1
                    WHERE a1.id = qz.article_id AND a1.is_published IS TRUE
                    UNION ALL
                    SELECT a2.id, a2.slug, a2.title, 1 AS prio
                    FROM {_SCHEMA}.kb_articles a2
                    WHERE a2.slug = ANY(q.tags) AND a2.is_published IS TRUE
                    ORDER BY prio, id
                    LIMIT 1
                ) a ON TRUE
                WHERE q.id = :question_id
                """
            ),
            {"question_id": question_id},
        )
    ).mappings().first()
    if not row:
        return None
    return {"id": int(row["id"]), "slug": str(row["slug"]), "title": str(row["title"])}


async def submit_training_answer(
    db: AsyncSession,
    *,
    operator_id: int,
    session_id: int,
    question_id: int,
    selected_option_ids: list[int],
) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)
    session = await _load_session(
        db, operator_id=operator_id, session_id=session_id, for_update=True
    )
    status = session["status"]
    if status == "abandoned":
        await db.commit()
        raise HTTPException(
            status_code=409,
            detail=f"Сессия завершена автоматически: нет ответов более {TRAINING_INACTIVITY_MINUTES} мин.",
        )
    if status != "in_progress":
        await db.commit()
        raise HTTPException(status_code=409, detail="Сессия уже завершена")

    current = session.get("current_question_id")
    if current is None or int(current) != int(question_id):
        await db.commit()
        raise HTTPException(status_code=409, detail="Вопрос уже не актуален — загрузите следующий")

    question = (
        await db.execute(
            text(
                f"""
                SELECT id, explanation
                FROM {_SCHEMA}.kb_questions
                WHERE id = :question_id
                """
            ),
            {"question_id": question_id},
        )
    ).mappings().first()
    if not question:
        await db.commit()
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    option_rows = (
        await db.execute(
            text(
                f"""
                SELECT id, is_correct
                FROM {_SCHEMA}.kb_question_options
                WHERE question_id = :question_id
                """
            ),
            {"question_id": question_id},
        )
    ).mappings().all()
    option_ids = {int(o["id"]) for o in option_rows}
    correct_ids = {int(o["id"]) for o in option_rows if o["is_correct"]}
    selected = {int(x) for x in selected_option_ids}
    if not selected or not selected.issubset(option_ids):
        await db.commit()
        raise HTTPException(status_code=400, detail="Выбраны варианты, не относящиеся к вопросу")
    is_correct = selected == correct_ids

    article = await _resolve_answer_article(db, question_id)

    await db.execute(
        text(
            f"""
            INSERT INTO {_SCHEMA}.kb_training_answers (
                session_id, question_id, article_id, selected_option_ids, is_correct
            ) VALUES (
                :session_id, :question_id, :article_id, CAST(:selected AS bigint[]), :is_correct
            )
            """
        ),
        {
            "session_id": session_id,
            "question_id": question_id,
            "article_id": article["id"] if article else None,
            "selected": sorted(selected),
            "is_correct": is_correct,
        },
    )
    # Очередь пуста — это был последний вопрос пула: все вопросы пройдены, сессия завершается.
    completed = not [int(x) for x in (session.get("question_queue") or [])]
    updated = (
        await db.execute(
            text(
                f"""
                UPDATE {_SCHEMA}.kb_training_sessions AS s
                SET
                    total_answers = s.total_answers + 1,
                    correct_count = s.correct_count + CASE WHEN :is_correct THEN 1 ELSE 0 END,
                    last_answer_at = NOW(),
                    current_question_id = NULL,
                    status = CASE
                        WHEN :completed THEN 'finished'::helpdesk.kb_training_session_status
                        ELSE s.status
                    END,
                    finished_at = CASE WHEN :completed THEN NOW() ELSE s.finished_at END
                WHERE s.id = :session_id
                RETURNING {_SESSION_COLUMNS}
                """
            ),
            {"session_id": session_id, "is_correct": is_correct, "completed": completed},
        )
    ).mappings().one()
    await db.commit()

    phones, emails = await load_manager_contact_lists(db)
    return {
        "is_correct": is_correct,
        "correct_option_ids": sorted(correct_ids),
        "explanation": substitute_manager_contacts(
            question.get("explanation"),
            phones=phones,
            emails=emails,
        ),
        "article": article,
        "completed": completed,
        "session": _session_state(dict(updated)),
    }


async def finish_training_session(
    db: AsyncSession,
    *,
    operator_id: int,
    session_id: int,
) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)
    session = await _load_session(
        db, operator_id=operator_id, session_id=session_id, for_update=True
    )
    if session["status"] == "in_progress":
        row = (
            await db.execute(
                text(
                    f"""
                    UPDATE {_SCHEMA}.kb_training_sessions AS s
                    SET
                        status = 'finished'::helpdesk.kb_training_session_status,
                        finished_at = NOW(),
                        current_question_id = NULL
                    WHERE s.id = :session_id
                    RETURNING {_SESSION_COLUMNS}
                    """
                ),
                {"session_id": session_id},
            )
        ).mappings().one()
        session = dict(row)
    await db.commit()
    return _session_state(session)


async def fetch_my_sessions(
    db: AsyncSession,
    *,
    operator_id: int,
    page: int,
    per_page: int,
) -> dict[str, Any]:
    await expire_stale_sessions(db, operator_id=operator_id)
    visible = "s.operator_id = :operator_id AND (s.total_answers > 0 OR s.status = 'in_progress')"

    totals = (
        await db.execute(
            text(
                f"""
                SELECT
                    COUNT(*)::int AS sessions_count,
                    COALESCE(SUM(s.total_answers), 0)::int AS total_answers,
                    COALESCE(SUM(s.correct_count), 0)::int AS correct_count,
                    COALESCE(
                        SUM(EXTRACT(EPOCH FROM (s.last_answer_at - s.started_at))),
                        0
                    )::bigint AS total_duration_sec
                FROM {_SCHEMA}.kb_training_sessions s
                WHERE {visible}
                """
            ),
            {"operator_id": operator_id},
        )
    ).mappings().one()

    rows = (
        await db.execute(
            text(
                f"""
                SELECT {_SESSION_COLUMNS}
                FROM {_SCHEMA}.kb_training_sessions s
                WHERE {visible}
                ORDER BY s.started_at DESC, s.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"operator_id": operator_id, "limit": per_page, "offset": (page - 1) * per_page},
        )
    ).mappings().all()
    await db.commit()

    total_answers = int(totals["total_answers"] or 0)
    correct = int(totals["correct_count"] or 0)
    return {
        "page": page,
        "per_page": per_page,
        "total": int(totals["sessions_count"] or 0),
        "totals": {
            "sessions_count": int(totals["sessions_count"] or 0),
            "total_answers": total_answers,
            "correct_count": correct,
            "score_percent": raw_percent(correct, total_answers),
            "total_duration_sec": int(totals["total_duration_sec"] or 0),
        },
        "items": [_session_list_item(dict(r)) for r in rows],
    }


# ---------------------------------------------------------------------------
# Администратор (support level=2) — подчинённые: support, активные, level=1
# (та же выборка, что в admin_quiz_stats_service).
# ---------------------------------------------------------------------------


async def is_training_admin(db: AsyncSession, user: dict[str, Any]) -> bool:
    row = await SkystreamUsersDAO.find_one_or_none(db, id=int(user["user_id"]))
    if not row:
        return False
    level = row.get("level")
    return stats_svc.is_support_admin(
        role=user.get("role"),
        level=int(level) if level is not None else None,
    )


async def find_subordinate(db: AsyncSession, operator_id: int) -> dict[str, Any] | None:
    trainees = await admin_quiz_svc._fetch_trainee_operators(db)
    return next((t for t in trainees if int(t["operator_id"]) == operator_id), None)


_TRAINEES_CTE = """
trainees AS (
    SELECT
        id AS operator_id,
        COALESCE(NULLIF(TRIM(full_name), ''), login) AS operator_name
    FROM users.skystream_users
    WHERE role = 'support'
      AND is_active IS TRUE
      AND level = 1
)
"""


async def _fetch_operator_period_rows(
    db: AsyncSession,
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                f"""
                WITH {_TRAINEES_CTE},
                period_answers AS (
                    SELECT s.operator_id, a.session_id, a.question_id, a.is_correct, a.answered_at
                    FROM {_SCHEMA}.kb_training_answers a
                    JOIN {_SCHEMA}.kb_training_sessions s ON s.id = a.session_id
                    JOIN trainees t ON t.operator_id = s.operator_id
                    WHERE a.answered_at >= :start AND a.answered_at < :end
                ),
                agg AS (
                    SELECT
                        operator_id,
                        COUNT(*)::int AS total,
                        COUNT(*) FILTER (WHERE is_correct)::int AS correct,
                        COUNT(DISTINCT question_id)::int AS coverage,
                        COUNT(DISTINCT session_id)::int AS sessions_count,
                        MAX(answered_at) AS last_activity_at
                    FROM period_answers
                    GROUP BY operator_id
                ),
                dur AS (
                    SELECT
                        s.operator_id,
                        SUM(EXTRACT(EPOCH FROM (s.last_answer_at - s.started_at)))::bigint AS duration_sec
                    FROM {_SCHEMA}.kb_training_sessions s
                    WHERE s.id IN (SELECT DISTINCT session_id FROM period_answers)
                      AND s.last_answer_at IS NOT NULL
                    GROUP BY s.operator_id
                ),
                active AS (
                    SELECT DISTINCT operator_id
                    FROM {_SCHEMA}.kb_training_sessions
                    WHERE status = 'in_progress'
                )
                SELECT
                    t.operator_id,
                    t.operator_name,
                    COALESCE(agg.total, 0) AS total,
                    COALESCE(agg.correct, 0) AS correct,
                    COALESCE(agg.coverage, 0) AS coverage,
                    COALESCE(agg.sessions_count, 0) AS sessions_count,
                    agg.last_activity_at,
                    COALESCE(dur.duration_sec, 0) AS duration_sec,
                    (active.operator_id IS NOT NULL) AS has_active_session
                FROM trainees t
                LEFT JOIN agg ON agg.operator_id = t.operator_id
                LEFT JOIN dur ON dur.operator_id = t.operator_id
                LEFT JOIN active ON active.operator_id = t.operator_id
                ORDER BY t.operator_name
                """
            ),
            {"start": start, "end": end},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def fetch_admin_summary(db: AsyncSession, *, date_from: date, date_to: date) -> dict[str, Any]:
    start, end = period_bounds(date_from, date_to)
    await expire_stale_sessions(db)
    rows = await _fetch_operator_period_rows(db, start=start, end=end)
    coverage = (
        await db.execute(
            text(
                f"""
                WITH {_TRAINEES_CTE}
                SELECT COUNT(DISTINCT a.question_id)::int
                FROM {_SCHEMA}.kb_training_answers a
                JOIN {_SCHEMA}.kb_training_sessions s ON s.id = a.session_id
                JOIN trainees t ON t.operator_id = s.operator_id
                WHERE a.answered_at >= :start AND a.answered_at < :end
                """
            ),
            {"start": start, "end": end},
        )
    ).scalar_one()
    await db.commit()

    total = sum(int(r["total"]) for r in rows)
    correct = sum(int(r["correct"]) for r in rows)
    return {
        "date_from": date_from,
        "date_to": date_to,
        "operators_count": len(rows),
        "active_operators_count": sum(1 for r in rows if int(r["total"]) > 0),
        "sessions_count": sum(int(r["sessions_count"]) for r in rows),
        "total_answers": total,
        "correct_count": correct,
        "avg_score_percent": raw_percent(correct, total),
        "total_duration_sec": sum(int(r["duration_sec"]) for r in rows),
        "coverage": int(coverage or 0),
    }


async def fetch_admin_leaders(db: AsyncSession, *, date_from: date, date_to: date) -> dict[str, Any]:
    start, end = period_bounds(date_from, date_to)
    await expire_stale_sessions(db)
    rows = await _fetch_operator_period_rows(db, start=start, end=end)
    await db.commit()
    board = build_leaderboard(rows, limit=LEADERS_LIMIT)
    return {"date_from": date_from, "date_to": date_to, **board}


async def fetch_admin_operators(db: AsyncSession, *, date_from: date, date_to: date) -> dict[str, Any]:
    start, end = period_bounds(date_from, date_to)
    await expire_stale_sessions(db)
    rows = await _fetch_operator_period_rows(db, start=start, end=end)
    await db.commit()
    items = []
    for r in rows:
        total = int(r["total"])
        correct = int(r["correct"])
        items.append(
            {
                "operator_id": int(r["operator_id"]),
                "operator_name": str(r["operator_name"] or ""),
                "sessions_count": int(r["sessions_count"]),
                "total_answers": total,
                "correct_count": correct,
                "score_percent": raw_percent(correct, total) if total > 0 else None,
                "coverage": int(r["coverage"]),
                "total_duration_sec": int(r["duration_sec"]),
                "last_activity_at": r.get("last_activity_at"),
                "has_active_session": bool(r.get("has_active_session")),
            }
        )
    return {"date_from": date_from, "date_to": date_to, "items": items}


async def fetch_admin_operator_sessions(
    db: AsyncSession,
    *,
    operator_id: int,
    date_from: date,
    date_to: date,
    page: int,
    per_page: int,
) -> dict[str, Any]:
    start, end = period_bounds(date_from, date_to)
    await expire_stale_sessions(db)
    in_period = f"""
        s.operator_id = :operator_id
        AND EXISTS (
            SELECT 1 FROM {_SCHEMA}.kb_training_answers a
            WHERE a.session_id = s.id
              AND a.answered_at >= :start AND a.answered_at < :end
        )
    """
    params: dict[str, Any] = {"operator_id": operator_id, "start": start, "end": end}
    total = (
        await db.execute(
            text(f"SELECT COUNT(*) FROM {_SCHEMA}.kb_training_sessions s WHERE {in_period}"),
            params,
        )
    ).scalar_one()
    rows = (
        await db.execute(
            text(
                f"""
                SELECT {_SESSION_COLUMNS}
                FROM {_SCHEMA}.kb_training_sessions s
                WHERE {in_period}
                ORDER BY s.started_at DESC, s.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": per_page, "offset": (page - 1) * per_page},
        )
    ).mappings().all()
    await db.commit()
    return {
        "date_from": date_from,
        "date_to": date_to,
        "page": page,
        "per_page": per_page,
        "total": int(total or 0),
        "items": [_session_list_item(dict(r)) for r in rows],
    }
