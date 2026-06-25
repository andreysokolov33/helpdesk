"""Ежедневный тест (daily warmup) для операторов КС."""

from __future__ import annotations

import json
import random
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.kb_service import _load_quiz_questions, _load_attempt_answered

_SCHEMA = "helpdesk"


def operator_requires_daily_quiz(*, role: str | None, level: int | None) -> bool:
    """Только role=support и level=1 проходят ежедневный тест."""
    return (role or "").strip().lower() == "support" and int(level or 0) == 1


def _local_now(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def _session_date(tz_name: str) -> date:
    return _local_now(tz_name).date()


def _in_time_window(
    *,
    local_now: datetime,
    show_from: time | None,
    show_until: time | None,
) -> bool:
    if show_from is None and show_until is None:
        return True
    current = local_now.time().replace(tzinfo=None)
    if show_from is not None and show_until is not None:
        return show_from <= current <= show_until
    if show_from is not None:
        return current >= show_from
    if show_until is not None:
        return current <= show_until
    return True


async def _load_active_policy(db: AsyncSession) -> dict[str, Any] | None:
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    p.id,
                    p.title,
                    p.weekdays,
                    p.timezone,
                    p.show_from_time,
                    p.show_until_time,
                    p.quiz_id,
                    p.questions_per_session,
                    p.passing_score_percent,
                    p.require_pass,
                    q.article_id
                FROM {_SCHEMA}.kb_daily_quiz_policies p
                JOIN {_SCHEMA}.kb_quizzes q ON q.id = p.quiz_id AND q.is_active IS TRUE
                WHERE p.is_active IS TRUE
                LIMIT 1
                """
            ),
        )
    ).mappings().first()
    return dict(row) if row else None


async def _load_today_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    session_date: date,
) -> dict[str, Any] | None:
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    id,
                    status::text AS status,
                    passed,
                    total_questions,
                    correct_count,
                    daily_policy_snapshot
                FROM {_SCHEMA}.kb_quiz_attempts
                WHERE operator_id = :operator_id
                  AND attempt_type = 'daily_warmup'
                  AND session_date = :session_date
                  AND status IN ('in_progress', 'finished')
                ORDER BY started_at DESC
                LIMIT 1
                """
            ),
            {"operator_id": operator_id, "session_date": session_date},
        )
    ).mappings().first()
    return dict(row) if row else None


async def _load_history(
    db: AsyncSession,
    *,
    operator_id: int,
    limit: int = 7,
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                f"""
                SELECT
                    session_date,
                    status::text AS status,
                    passed,
                    correct_count,
                    total_questions
                FROM {_SCHEMA}.kb_quiz_attempts
                WHERE operator_id = :operator_id
                  AND attempt_type = 'daily_warmup'
                  AND session_date IS NOT NULL
                  AND status = 'finished'
                ORDER BY session_date DESC
                LIMIT :limit
                """
            ),
            {"operator_id": operator_id, "limit": limit},
        )
    ).mappings().all()
    out: list[dict[str, Any]] = []
    for r in rows:
        sd = r["session_date"]
        if isinstance(sd, datetime):
            sd = sd.date()
        out.append(
            {
                "session_date": sd,
                "day_label": str(int(sd.day)),
                "passed": bool(r["passed"]) if r["passed"] is not None else None,
                "status": str(r["status"]),
                "correct_count": int(r.get("correct_count") or 0),
                "total_questions": int(r.get("total_questions") or 0),
            }
        )
    return out


def _policy_allows_today(policy: dict[str, Any]) -> tuple[date, bool]:
    tz_name = str(policy.get("timezone") or "Europe/Moscow")
    local = _local_now(tz_name)
    session_day = local.date()
    weekdays = list(policy.get("weekdays") or [])
    iso_dow = local.isoweekday()
    weekday_ok = iso_dow in weekdays
    time_ok = _in_time_window(
        local_now=local,
        show_from=policy.get("show_from_time"),
        show_until=policy.get("show_until_time"),
    )
    return session_day, bool(weekday_ok and time_ok)


async def fetch_daily_quiz_status(
    db: AsyncSession,
    *,
    operator_id: int,
    role: str | None,
    level: int | None,
) -> dict[str, Any]:
    history = await _load_history(db, operator_id=operator_id)
    if not operator_requires_daily_quiz(role=role, level=level):
        return {
            "required": False,
            "show_modal": False,
            "session_date": None,
            "attempt_id": None,
            "attempt_status": "none",
            "title": None,
            "questions_per_session": None,
            "history": history,
        }

    policy = await _load_active_policy(db)
    if not policy:
        return {
            "required": True,
            "show_modal": False,
            "session_date": None,
            "attempt_id": None,
            "attempt_status": "none",
            "title": None,
            "questions_per_session": None,
            "history": history,
        }

    session_day, schedule_ok = _policy_allows_today(policy)
    today_attempt = await _load_today_attempt(
        db, operator_id=operator_id, session_date=session_day
    )

    show_modal = schedule_ok
    attempt_id: int | None = None
    attempt_status = "none"
    if today_attempt:
        attempt_status = str(today_attempt["status"])
        attempt_id = int(today_attempt["id"])
        if attempt_status == "finished":
            show_modal = False

    return {
        "required": True,
        "show_modal": show_modal,
        "session_date": session_day,
        "attempt_id": attempt_id,
        "attempt_status": attempt_status,
        "title": str(policy.get("title") or "Ежедневный тест"),
        "questions_per_session": int(policy.get("questions_per_session") or 5),
        "history": history,
    }


def _questions_by_ids(
    all_questions: list[dict[str, Any]],
    question_ids: list[int],
) -> list[dict[str, Any]]:
    by_id = {int(q["id"]): q for q in all_questions}
    return [by_id[qid] for qid in question_ids if qid in by_id]


def _pick_question_ids(all_questions: list[dict[str, Any]], count: int) -> list[int]:
    ids = [int(q["id"]) for q in all_questions]
    if not ids:
        return []
    n = min(max(count, 1), len(ids))
    return random.sample(ids, n)


async def _load_questions_for_attempt(
    db: AsyncSession,
    *,
    quiz_id: int,
    snapshot: dict[str, Any] | None,
    questions_per_session: int,
) -> list[dict[str, Any]]:
    all_questions = await _load_quiz_questions(db, quiz_id)
    if snapshot and snapshot.get("question_ids"):
        return _questions_by_ids(all_questions, [int(x) for x in snapshot["question_ids"]])
    return _questions_by_ids(
        all_questions,
        _pick_question_ids(all_questions, questions_per_session),
    )


async def fetch_daily_quiz_session(
    db: AsyncSession,
    *,
    operator_id: int,
    role: str | None,
    level: int | None,
) -> dict[str, Any]:
    if not operator_requires_daily_quiz(role=role, level=level):
        raise HTTPException(status_code=403, detail="Ежедневный тест не требуется")

    policy = await _load_active_policy(db)
    if not policy:
        raise HTTPException(status_code=404, detail="Политика ежедневного теста не настроена")

    session_day, schedule_ok = _policy_allows_today(policy)
    if not schedule_ok:
        raise HTTPException(status_code=403, detail="Сейчас не время для ежедневного теста")

    quiz_id = int(policy["quiz_id"])
    article_id = int(policy["article_id"])
    today_attempt = await _load_today_attempt(
        db, operator_id=operator_id, session_date=session_day
    )

    snapshot: dict[str, Any] | None = None
    if today_attempt:
        raw = today_attempt.get("daily_policy_snapshot")
        if isinstance(raw, dict):
            snapshot = raw
        elif isinstance(raw, str):
            try:
                snapshot = json.loads(raw)
            except json.JSONDecodeError:
                snapshot = None

    questions = await _load_questions_for_attempt(
        db,
        quiz_id=quiz_id,
        snapshot=snapshot,
        questions_per_session=int(policy.get("questions_per_session") or 5),
    )

    answered: list[dict[str, Any]] = []
    attempt_id: int | None = None
    attempt_status = "none"
    passed: bool | None = None
    correct_count: int | None = None

    if today_attempt:
        attempt_id = int(today_attempt["id"])
        attempt_status = str(today_attempt["status"])
        if attempt_status == "finished":
            passed = bool(today_attempt["passed"])
            correct_count = int(today_attempt.get("correct_count") or 0)
        elif attempt_status == "in_progress":
            answered = await _load_attempt_answered(db, attempt_id=attempt_id)

    return {
        "quiz_id": quiz_id,
        "article_id": article_id,
        "title": str(policy.get("title") or "Ежедневный тест"),
        "passing_score_percent": int(policy.get("passing_score_percent") or 100),
        "session_date": session_day,
        "attempt_id": attempt_id,
        "attempt_status": attempt_status,
        "passed": passed,
        "total_questions": len(questions),
        "correct_count": correct_count,
        "questions": questions,
        "answered": answered,
    }


async def start_daily_quiz_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    role: str | None,
    level: int | None,
) -> dict[str, Any]:
    if not operator_requires_daily_quiz(role=role, level=level):
        raise HTTPException(status_code=403, detail="Ежедневный тест не требуется")

    policy = await _load_active_policy(db)
    if not policy:
        raise HTTPException(status_code=404, detail="Политика ежедневного теста не настроена")

    session_day, schedule_ok = _policy_allows_today(policy)
    if not schedule_ok:
        raise HTTPException(status_code=403, detail="Сейчас не время для ежедневного теста")

    existing = await _load_today_attempt(
        db, operator_id=operator_id, session_date=session_day
    )
    if existing:
        status = str(existing["status"])
        if status == "finished":
            raise HTTPException(status_code=409, detail="Тест на сегодня уже завершён")
        return {
            "attempt_id": int(existing["id"]),
            "total_questions": int(existing["total_questions"]),
        }

    quiz_id = int(policy["quiz_id"])
    article_id = int(policy["article_id"])
    per_session = int(policy.get("questions_per_session") or 5)
    all_questions = await _load_quiz_questions(db, quiz_id)
    question_ids = _pick_question_ids(all_questions, per_session)
    if not question_ids:
        raise HTTPException(status_code=400, detail="В пуле ежедневного теста нет вопросов")

    snapshot = {
        "policy_id": int(policy["id"]),
        "question_ids": question_ids,
        "passing_score_percent": int(policy.get("passing_score_percent") or 100),
        "require_pass": bool(policy.get("require_pass")),
    }

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
                    total_questions, content_version, session_date,
                    daily_policy_id, daily_policy_snapshot
                ) VALUES (
                    :operator_id, :quiz_id, :article_id,
                    'daily_warmup'::helpdesk.kb_quiz_attempt_type,
                    'in_progress'::helpdesk.kb_quiz_attempt_status,
                    :total_questions, :version, :session_date,
                    :policy_id, CAST(:snapshot AS jsonb)
                )
                RETURNING id
                """
            ),
            {
                "operator_id": operator_id,
                "quiz_id": quiz_id,
                "article_id": article_id,
                "total_questions": len(question_ids),
                "version": int(version),
                "session_date": session_day,
                "policy_id": int(policy["id"]),
                "snapshot": json.dumps(snapshot, ensure_ascii=False),
            },
        )
    ).scalar_one()
    await db.commit()
    return {"attempt_id": int(attempt_id), "total_questions": len(question_ids)}
