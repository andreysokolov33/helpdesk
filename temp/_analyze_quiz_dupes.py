"""Analyze kb quiz questions for duplicated text and multicast wording."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

DUPE_FULL_REPEAT_RE = re.compile(r"^(.+?)(\d+\.\s*)(\1)$", re.DOTALL)
MULTICAST_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Мультикасте", re.IGNORECASE), "Медиасервере"),
    (re.compile(r"Мультикаста", re.IGNORECASE), "Медиасервера"),
    (re.compile(r"Мультикасту", re.IGNORECASE), "Медиасерверу"),
    (re.compile(r"Мультикаст", re.IGNORECASE), "Медиасервер"),
]


@dataclass
class QuestionRow:
    quiz_id: int
    quiz_title: str
    question_id: int
    question_text: str
    explanation: str | None


def dedupe_question_text(text_value: str) -> str | None:
    text_value = text_value.strip()
    if not text_value:
        return None

    m = DUPE_FULL_REPEAT_RE.match(text_value)
    if m:
        return m.group(1).strip()

    half = len(text_value) // 2
    if len(text_value) % 2 == 0 and text_value[:half] == text_value[half:]:
        return text_value[:half].strip()

    for dup_len in range(len(text_value) // 2, 0, -1):
        tail = text_value[-dup_len:]
        prev = text_value[-2 * dup_len : -dup_len]
        if tail != prev:
            continue
        if dup_len >= 10 or "?" in tail or re.search(r"\d+\.\s", text_value):
            return text_value[:-dup_len].strip()

    for i, ch in enumerate(text_value):
        if ch != "?":
            continue
        head = text_value[: i + 1]
        tail = text_value[i + 1 :].lstrip()
        tail = re.sub(r"^\d+\.\s*", "", tail)
        if tail and head.endswith(tail):
            return head.strip()

    return None


def replace_multicast(text_value: str) -> str | None:
    updated = text_value
    changed = False
    for pattern, replacement in MULTICAST_REPLACEMENTS:
        new_value = pattern.sub(replacement, updated)
        if new_value != updated:
            changed = True
            updated = new_value
    return updated if changed else None


def fix_text(text_value: str, *, allow_dedupe: bool = True) -> tuple[str, list[str]]:
    notes: list[str] = []
    current = text_value

    if allow_dedupe:
        while True:
            deduped = dedupe_question_text(current)
            if not deduped or deduped == current:
                break
            notes.append("dedupe")
            current = deduped

    replaced = replace_multicast(current)
    if replaced and replaced != current:
        notes.append("multicast")
        current = replaced

    return current, notes


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                """
                SELECT q.id AS quiz_id, q.title AS quiz_title,
                       qq.id AS question_id, qq.question_text, qq.explanation
                FROM helpdesk.kb_quizzes q
                JOIN helpdesk.kb_questions qq ON qq.quiz_id = q.id
                ORDER BY q.id, qq.sort_order, qq.id
                """
            )
        )
        questions = [
            QuestionRow(
                quiz_id=r.quiz_id,
                quiz_title=r.quiz_title,
                question_id=r.question_id,
                question_text=r.question_text or "",
                explanation=r.explanation,
            )
            for r in rows.fetchall()
        ]

        option_rows = await conn.execute(
            text(
                """
                SELECT o.id, o.question_id, o.option_text
                FROM helpdesk.kb_question_options o
                JOIN helpdesk.kb_questions qq ON qq.id = o.question_id
                ORDER BY o.question_id, o.sort_order, o.id
                """
            )
        )
        options = option_rows.fetchall()

    await engine.dispose()

    updates: list[str] = []
    updates.append("-- Автогенерация: исправление дублей вопросов и замена «Мультикаст» → «Медиасервер»")
    updates.append("-- Проверьте скрипт перед применением на проде.")
    updates.append("BEGIN;")
    updates.append("")

    quiz_titles_fixed: dict[int, tuple[str, str]] = {}
    question_fixes = 0
    explanation_fixes = 0
    option_fixes = 0

    for q in questions:
        fixed, notes = fix_text(q.question_text)
        if fixed != q.question_text:
            question_fixes += 1
            updates.append(
                f"-- quiz_id={q.quiz_id} «{q.quiz_title}» | question_id={q.question_id} | {', '.join(notes)}"
            )
            updates.append(
                f"-- было: {q.question_text}"
            )
            updates.append(
                f"UPDATE helpdesk.kb_questions SET question_text = {sql_literal(fixed)}, updated_at = NOW() WHERE id = {q.question_id};"
            )
            updates.append("")

        if q.explanation:
            fixed_expl, expl_notes = fix_text(q.explanation, allow_dedupe=False)
            if fixed_expl != q.explanation:
                explanation_fixes += 1
                updates.append(
                    f"-- explanation question_id={q.question_id} | {', '.join(expl_notes)}"
                )
                updates.append(
                    f"UPDATE helpdesk.kb_questions SET explanation = {sql_literal(fixed_expl)}, updated_at = NOW() WHERE id = {q.question_id};"
                )
                updates.append("")

        fixed_title, title_notes = fix_text(q.quiz_title)
        if fixed_title != q.quiz_title and q.quiz_id not in quiz_titles_fixed:
            quiz_titles_fixed[q.quiz_id] = (q.quiz_title, fixed_title)

    for quiz_id, (old_title, new_title) in sorted(quiz_titles_fixed.items()):
        updates.append(f"-- quiz_id={quiz_id} title | было: {old_title}")
        updates.append(
            f"UPDATE helpdesk.kb_quizzes SET title = {sql_literal(new_title)}, updated_at = NOW() WHERE id = {quiz_id};"
        )
        updates.append("")

    for opt in options:
        fixed, notes = fix_text(opt.option_text or "", allow_dedupe=False)
        if fixed != (opt.option_text or ""):
            option_fixes += 1
            updates.append(
                f"-- option_id={opt.id} question_id={opt.question_id} | {', '.join(notes)}"
            )
            updates.append(
                f"UPDATE helpdesk.kb_question_options SET option_text = {sql_literal(fixed)} WHERE id = {opt.id};"
            )
            updates.append("")

    updates.append("COMMIT;")
    updates.append("")

    out_path = "/home/sokolov/development/helpdesk/temp/ipdate-database.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(updates))

    print(f"Questions scanned: {len(questions)}")
    print(f"Question text fixes: {question_fixes}")
    print(f"Explanation fixes: {explanation_fixes}")
    print(f"Quiz title fixes: {len(quiz_titles_fixed)}")
    print(f"Option fixes: {option_fixes}")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
