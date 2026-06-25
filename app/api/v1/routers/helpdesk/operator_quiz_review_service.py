"""Просмотр и практика по завершённым попыткам тестов."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.helpdesk.daily_quiz_service import (
    _load_questions_for_attempt,
    _questions_by_ids,
)
from app.api.v1.routers.helpdesk.kb_service import (
    _load_attempt_answered,
    _load_quiz_questions,
    apply_contacts_to_quiz_questions,
    load_manager_contact_lists,
)
from app.api.v1.routers.helpdesk.manager_contacts_service import substitute_manager_contacts

_SCHEMA = "helpdesk"


def _score_percent(correct: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(round((correct / total) * 100))


def _parse_snapshot(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def is_practice_snapshot(snapshot: dict[str, Any] | None) -> bool:
    return bool(snapshot and snapshot.get("practice"))


async def _load_finished_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    attempt_id: int,
) -> dict[str, Any]:
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    qa.id,
                    qa.operator_id,
                    qa.quiz_id,
                    qa.article_id,
                    qa.attempt_type::text AS attempt_type,
                    qa.status::text AS status,
                    qa.session_date,
                    qa.finished_at,
                    qa.correct_count,
                    qa.total_questions,
                    qa.passed,
                    qa.daily_policy_snapshot,
                    qa.daily_policy_id,
                    a.slug AS article_slug,
                    a.title AS article_title,
                    c.title AS category_title,
                    q.passing_score_percent
                FROM {_SCHEMA}.kb_quiz_attempts qa
                JOIN {_SCHEMA}.kb_articles a ON a.id = qa.article_id
                LEFT JOIN {_SCHEMA}.kb_categories c ON c.id = a.category_id
                JOIN {_SCHEMA}.kb_quizzes q ON q.id = qa.quiz_id
                WHERE qa.id = :attempt_id
                  AND qa.operator_id = :operator_id
                """
            ),
            {"attempt_id": attempt_id, "operator_id": operator_id},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    return dict(row)


async def _question_ids_for_attempt(
    db: AsyncSession,
    *,
    attempt: dict[str, Any],
) -> list[int]:
    snapshot = _parse_snapshot(attempt.get("daily_policy_snapshot"))
    if snapshot.get("question_ids"):
        return [int(x) for x in snapshot["question_ids"]]

    rows = (
        await db.execute(
            text(
                f"""
                SELECT question_id
                FROM {_SCHEMA}.kb_quiz_attempt_answers
                WHERE attempt_id = :attempt_id
                ORDER BY answered_at, id
                """
            ),
            {"attempt_id": int(attempt["id"])},
        )
    ).scalars().all()
    return [int(x) for x in rows]


async def _load_review_questions(
    db: AsyncSession,
    *,
    attempt: dict[str, Any],
) -> list[dict[str, Any]]:
    quiz_id = int(attempt["quiz_id"])
    snapshot = _parse_snapshot(attempt.get("daily_policy_snapshot"))
    question_ids = await _question_ids_for_attempt(db, attempt=attempt)

    if question_ids:
        all_questions = await _load_quiz_questions(db, quiz_id)
        questions = _questions_by_ids(all_questions, question_ids)
    else:
        questions = await _load_questions_for_attempt(
            db,
            quiz_id=quiz_id,
            snapshot=snapshot or None,
            questions_per_session=int(attempt.get("total_questions") or 0) or 5,
        )

    phones, emails = await load_manager_contact_lists(db)
    return apply_contacts_to_quiz_questions(
        questions,
        phones=phones,
        emails=emails,
    )


async def _enrich_answered_with_explanations(
    db: AsyncSession,
    *,
    answered: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not answered:
        return []
    q_ids = [int(a["question_id"]) for a in answered]
    rows = (
        await db.execute(
            text(
                f"""
                SELECT id, explanation
                FROM {_SCHEMA}.kb_questions
                WHERE id = ANY(:q_ids)
                """
            ),
            {"q_ids": q_ids},
        )
    ).mappings().all()
    phones, emails = await load_manager_contact_lists(db)
    expl_by_id = {
        int(r["id"]): substitute_manager_contacts(
            r.get("explanation"),
            phones=phones,
            emails=emails,
        )
        for r in rows
    }
    out: list[dict[str, Any]] = []
    for a in answered:
        item = dict(a)
        item["explanation"] = expl_by_id.get(int(a["question_id"]))
        out.append(item)
    return out


async def fetch_attempt_review(
    db: AsyncSession,
    *,
    operator_id: int,
    attempt_id: int,
) -> dict[str, Any]:
    attempt = await _load_finished_attempt(
        db, operator_id=operator_id, attempt_id=attempt_id
    )
    if str(attempt["status"]) != "finished":
        raise HTTPException(status_code=409, detail="Попытка ещё не завершена")
    if is_practice_snapshot(_parse_snapshot(attempt.get("daily_policy_snapshot"))):
        raise HTTPException(status_code=404, detail="Попытка не найдена")

    questions = await _load_review_questions(db, attempt=attempt)
    answered = await _enrich_answered_with_explanations(
        db,
        answered=await _load_attempt_answered(db, attempt_id=attempt_id),
    )

    correct = int(attempt.get("correct_count") or 0)
    total = int(attempt.get("total_questions") or 0)
    return {
        "attempt_id": int(attempt["id"]),
        "attempt_type": str(attempt["attempt_type"]),
        "finished_at": attempt.get("finished_at"),
        "session_date": attempt.get("session_date"),
        "article_slug": attempt.get("article_slug"),
        "article_title": attempt.get("article_title"),
        "category_title": attempt.get("category_title"),
        "correct_count": correct,
        "total_questions": total,
        "score_percent": _score_percent(correct, total),
        "passed": bool(attempt.get("passed")),
        "passing_score_percent": int(attempt.get("passing_score_percent") or 100),
        "questions": questions,
        "answered": answered,
    }


async def start_practice_attempt(
    db: AsyncSession,
    *,
    operator_id: int,
    source_attempt_id: int,
) -> dict[str, Any]:
    source = await _load_finished_attempt(
        db, operator_id=operator_id, attempt_id=source_attempt_id
    )
    if str(source["status"]) != "finished":
        raise HTTPException(status_code=409, detail="Можно повторить только завершённый тест")
    if is_practice_snapshot(_parse_snapshot(source.get("daily_policy_snapshot"))):
        raise HTTPException(status_code=400, detail="Практика строится только по официальной попытке")

    question_ids = await _question_ids_for_attempt(db, attempt=source)
    if not question_ids:
        raise HTTPException(status_code=400, detail="Не удалось восстановить вопросы теста")

    base_snapshot = _parse_snapshot(source.get("daily_policy_snapshot"))
    practice_snapshot = {
        **base_snapshot,
        "practice": True,
        "source_attempt_id": int(source_attempt_id),
        "question_ids": question_ids,
        "passing_score_percent": int(
            base_snapshot.get("passing_score_percent")
            or source.get("passing_score_percent")
            or 100
        ),
    }

    await db.execute(
        text(
            f"""
            UPDATE {_SCHEMA}.kb_quiz_attempts
            SET status = 'abandoned'::helpdesk.kb_quiz_attempt_status
            WHERE operator_id = :operator_id
              AND status = 'in_progress'
              AND daily_policy_snapshot->>'practice' = 'true'
              AND daily_policy_snapshot->>'source_attempt_id' = :source_id
            """
        ),
        {"operator_id": operator_id, "source_id": str(source_attempt_id)},
    )

    article_id = int(source["article_id"])
    quiz_id = int(source["quiz_id"])
    version = (
        await db.execute(
            text(f"SELECT version FROM {_SCHEMA}.kb_articles WHERE id = :id"),
            {"id": article_id},
        )
    ).scalar_one()

    attempt_type = str(source["attempt_type"])
    session_date = None

    new_id = (
        await db.execute(
            text(
                f"""
                INSERT INTO {_SCHEMA}.kb_quiz_attempts (
                    operator_id, quiz_id, article_id, attempt_type, status,
                    total_questions, content_version, session_date,
                    daily_policy_id, daily_policy_snapshot
                ) VALUES (
                    :operator_id, :quiz_id, :article_id,
                    :attempt_type::helpdesk.kb_quiz_attempt_type,
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
                "attempt_type": attempt_type,
                "total_questions": len(question_ids),
                "version": int(version),
                "session_date": session_date,
                "policy_id": source.get("daily_policy_id"),
                "snapshot": json.dumps(practice_snapshot, ensure_ascii=False),
            },
        )
    ).scalar_one()
    await db.commit()
    return {"attempt_id": int(new_id), "total_questions": len(question_ids)}
