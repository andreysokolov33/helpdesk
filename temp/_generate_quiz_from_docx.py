#!/usr/bin/env python3
"""Генерация SQL из temp/database/Тестирование (список всех вопросов).docx"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "database" / "Тестирование (список всех вопросов).docx"
OUT = ROOT / "quiz-from-docx.sql"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
OPTION_RE = re.compile(r"^([А-Г])\)\s*(.+)$")
THEME_RE = re.compile(r"^Тема\s+(\d+)\.\s*(.+)$")
ANSWER_RE = re.compile(r"^Правильный ответ:\s*([А-Г])\s*$")
EXPLAIN_RE = re.compile(r"^Разбор:\s*(.+)$")
SEP_RE = re.compile(r"^─+$")

LETTER_ORDER = {"А": 0, "Б": 10, "В": 20, "Г": 30}

THEME_TO_SLUG: dict[int, str | None] = {
    1: "kak-otrabatyvat-zhaloby",
    2: "mediakontent-videoservis-multikast",
    3: "finansovye-voprosy-i-dokumenty",
    4: "organizatsionnye-voprosy",
    5: "lichnyy-kabinet-i-dostup",
    6: "vosstanovlenie-trafika",
    7: "turbo-knopka",
    8: "sutochnyy-sbros-obnovlenie-trafika",
    9: "zamorozka-razmorozka-tarifa",
    10: "smena-tarifa",
    11: "oplatil-no-dengi-ne-prishli",
    12: "trebovanie-vozvrata-deneg",
    13: "net-podklyucheniya-k-internetu",
    14: None,  # split by keywords
    15: "glossariy-terminov",
    16: None,  # keyword routing
    17: "lineyki-tarifov",
    18: "novye-podklyucheniya",
    19: "razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov",
}

THEME16_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"трафик|glasswire|передач[аи] данных", re.I), "kuda-uhodit-trafik"),
    (re.compile(r"парол|робот|восстанов", re.I), "lichnyy-kabinet-i-dostup"),
    (re.compile(r"роутер|pppoE|оборудован|кабел", re.I), "problemy-s-oborudovaniem"),
    (re.compile(r"замороз", re.I), "zamorozka-razmorozka-tarifa"),
    (re.compile(r"скорост|обрыв", re.I), "nizkaya-skorost-obryvy"),
    (re.compile(r"оплат|платеж|баланс|списан", re.I), "voprosy-po-spisaniyam-i-rashodam"),
    (re.compile(r"возражен", re.I), "kak-otvechat-na-vozrazheniya"),
    (re.compile(r"заявк|инженер", re.I), "kak-sobrat-dannye-dlya-zayavki"),
]


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def para_text(p: ET.Element) -> str:
    parts: list[str] = []
    for t in p.findall(".//w:t", NS):
        if t.text:
            parts.append(t.text)
        if t.tail:
            parts.append(t.tail)
    return "".join(parts).strip()


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    for length in range(min(100, len(text) // 2), 12, -1):
        chunk = text[:length]
        if text[length : length + length] == chunk:
            return chunk + text[length + length :]
    return text


def slug_for_question(theme_num: int, question: str, explanation: str) -> str | None:
    blob = f"{question} {explanation}".lower()
    if theme_num == 14:
        if re.search(r"ркн|whatsapp|youtube|блокир|замедлен", blob):
            return "rkn-blokirovki-i-ogranicheniya-dostupa"
        return "sroki-otveta-inzhenerov"
    if theme_num == 16:
        for pattern, slug in THEME16_RULES:
            if pattern.search(blob):
                return slug
        return "kak-sobrat-dannye-dlya-zayavki"
    return THEME_TO_SLUG.get(theme_num)


def load_paragraphs() -> list[str]:
    with zipfile.ZipFile(DOCX) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    paras = [para_text(p) for p in root.findall(".//w:p", NS)]
    return [p for p in paras if p and p != "Единый тест для операторов контакт-центра"]


def parse_questions(paras: list[str]) -> list[dict]:
    questions: list[dict] = []
    current_theme_num: int | None = None
    current_theme: str | None = None
    i = 0
    while i < len(paras):
        p = paras[i]
        m = THEME_RE.match(p)
        if m:
            current_theme_num = int(m.group(1))
            title = m.group(2).strip()
            if "Тема " in title and title.index("Тема ") > 0:
                title = title[: title.index("Тема ")].strip()
            current_theme = title
            i += 1
            continue
        if SEP_RE.match(p):
            i += 1
            continue
        if i + 1 < len(paras) and OPTION_RE.match(paras[i + 1]):
            qtext = clean_text(p)
            i += 1
            options: list[tuple[str, str]] = []
            while i < len(paras) and OPTION_RE.match(paras[i]):
                om = OPTION_RE.match(paras[i])
                assert om is not None
                options.append((om.group(1), clean_text(om.group(2))))
                i += 1
            am = ANSWER_RE.match(paras[i])
            if not am:
                raise ValueError(f"Expected answer line, got: {paras[i]!r}")
            correct = am.group(1)
            i += 1
            explanation = ""
            if i < len(paras):
                em = EXPLAIN_RE.match(paras[i])
                if em:
                    explanation = clean_text(em.group(1))
                    i += 1
            slug = slug_for_question(current_theme_num or 0, qtext, explanation)
            questions.append(
                {
                    "theme_num": current_theme_num,
                    "theme": current_theme,
                    "slug": slug,
                    "question": qtext,
                    "options": options,
                    "correct": correct,
                    "explanation": explanation,
                }
            )
            continue
        i += 1
    return questions


def slug_sort_key(slug: str) -> tuple[str, str]:
    return (slug, "")


def emit_delete(slugs: set[str]) -> list[str]:
    slug_list = ", ".join(sql_literal(s) for s in sorted(slugs))
    return [
        "-- Очистка перед переимпортом: попытки ссылаются на вопросы (RESTRICT)",
        f"""
UPDATE helpdesk.kb_article_progress p
SET last_attempt_id = NULL, updated_at = NOW()
WHERE p.last_attempt_id IN (
    SELECT qa.id
    FROM helpdesk.kb_quiz_attempts qa
    JOIN helpdesk.kb_articles a ON a.id = qa.article_id
    WHERE a.slug IN ({slug_list})
);
""".strip(),
        f"""
DELETE FROM helpdesk.kb_quiz_attempts qa
USING helpdesk.kb_articles a
WHERE qa.article_id = a.id
  AND a.slug IN ({slug_list});
""".strip(),
        "-- Ответы на вопросы удаляются каскадом с попытками; варианты — с вопросами",
        f"""
DELETE FROM helpdesk.kb_questions qq
USING helpdesk.kb_quizzes q, helpdesk.kb_articles a
WHERE qq.quiz_id = q.id
  AND q.article_id = a.id
  AND a.slug IN ({slug_list});
""".strip(),
    ]


def emit_ensure_quiz(slug: str, title: str) -> list[str]:
    return [
        f"-- Квиз: {title}",
        f"""
INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, {sql_literal(f'Проверка знаний: {title}')}, '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = {sql_literal(slug)}
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);
""".strip(),
    ]


def emit_question(
    slug: str,
    question: dict,
    sort_order: int,
    tag: str,
) -> list[str]:
    qtext = question["question"]
    expl = question["explanation"]
    correct = question["correct"]
    lines: list[str] = []
    lines.append(
        f"""
INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, {sql_literal(qtext)}, {sql_literal(expl)},
       'single'::helpdesk.kb_question_selection_mode, {sort_order}, TRUE,
       ARRAY[{sql_literal(tag)}]::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = {sql_literal(slug)}
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = {sql_literal(qtext)}
  );
""".strip()
    )
    for letter, opt_text in question["options"]:
        is_correct = "TRUE" if letter == correct else "FALSE"
        sort = LETTER_ORDER.get(letter, 0)
        lines.append(
            f"""
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, {sql_literal(opt_text)}, {is_correct}, {sort}
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = {sql_literal(slug)}
  AND qq.question_text = {sql_literal(qtext)}
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = {sql_literal(opt_text)}
  );
""".strip()
        )
    return lines


def main() -> None:
    paras = load_paragraphs()
    questions = parse_questions(paras)
    if len(questions) != 171:
        raise SystemExit(f"Expected 171 questions, parsed {len(questions)}")

    by_slug: dict[str, list[dict]] = defaultdict(list)
    for q in questions:
        slug = q["slug"]
        if slug:
            by_slug[slug].append(q)

    all_slugs = set(by_slug) | {"daily-warmup"}

    out: list[str] = [
        "-- =============================================================================",
        "-- Квизы из: temp/database/Тестирование (список всех вопросов).docx",
        f"-- Вопросов: {len(questions)} | Тем: 19 | Статей: {len(by_slug)} + daily-warmup",
        "-- Сгенерировано: temp/_generate_quiz_from_docx.py",
        "--",
        "-- Если ошибка 25P02 (transaction aborted): выполните ROLLBACK; и запустите снова.",
        "-- =============================================================================",
        "",
        "-- Сброс прерванной транзакции в текущей сессии (безопасно, если транзакции нет)",
        "ROLLBACK;",
        "",
        "BEGIN;",
        "",
    ]

    out.extend(emit_delete(all_slugs))

    out.append("")
    out.append("-- Служебная статья и квиз для ежедневного теста (если ещё нет)")
    out.append(
        """
INSERT INTO helpdesk.kb_articles (
    category_id, title, slug, summary, content_html, content_format, sidebar_json,
    sort_order, is_published, quiz_required
)
SELECT
    COALESCE(
        (SELECT id FROM helpdesk.kb_categories WHERE slug = 'spravochnye-materialy' AND is_active LIMIT 1),
        (SELECT id FROM helpdesk.kb_categories WHERE is_active
         ORDER BY helpdesk.kb_categories.sort_order, helpdesk.kb_categories.id LIMIT 1)
    ),
    'Ежедневная разминка', 'daily-warmup',
    'Пул вопросов ежедневного теста.',
    '<div class="section-card"><p>Служебная статья.</p></div>',
    'html'::helpdesk.kb_content_format, '{}'::jsonb, 9999, FALSE, FALSE
WHERE NOT EXISTS (SELECT 1 FROM helpdesk.kb_articles WHERE slug = 'daily-warmup');
""".strip()
    )
    out.extend(emit_ensure_quiz("daily-warmup", "Ежедневная разминка"))

    out.append("")
    out.append("-- -----------------------------------------------------------------------------")
    out.append("-- Вопросы по статьям /kb (по темам)")
    out.append("-- -----------------------------------------------------------------------------")

    for slug in sorted(by_slug):
        items = by_slug[slug]
        theme_name = items[0].get("theme") or slug
        out.append("")
        out.extend(emit_ensure_quiz(slug, theme_name))
        for idx, q in enumerate(items, start=1):
            out.extend(emit_question(slug, q, idx * 10, slug))

    out.append("")
    out.append("-- -----------------------------------------------------------------------------")
    out.append("-- Полный пул в daily-warmup (все 171 вопроса для ежедневного теста)")
    out.append("-- -----------------------------------------------------------------------------")
    for idx, q in enumerate(questions, start=1):
        tag = q["slug"] or f"theme-{q['theme_num']}"
        out.extend(emit_question("daily-warmup", q, idx * 10, tag))

    out.append("")
    out.append("-- Политика ежедневного теста (обновить quiz_id, если политика уже есть)")
    out.append(
        """
UPDATE helpdesk.kb_daily_quiz_policies p
SET quiz_id = q.id, updated_at = NOW()
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND p.is_active;

INSERT INTO helpdesk.kb_daily_quiz_policies (
    title, is_active, weekdays, timezone, quiz_id,
    questions_per_session, passing_score_percent, is_blocking, allow_skip, require_pass
)
SELECT 'Ежедневный тест при входе', TRUE, '{1,2,3,4,5,6,7}'::SMALLINT[],
       'Europe/Moscow', q.id, 5, 100, TRUE, FALSE, FALSE
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_daily_quiz_policies WHERE is_active);
""".strip()
    )

    out.append("")
    out.append("COMMIT;")
    out.append("")
    out.append("-- Статистика после импорта:")
    out.append(
        """
-- SELECT a.slug, COUNT(qq.id) AS questions
-- FROM helpdesk.kb_articles a
-- JOIN helpdesk.kb_quizzes q ON q.article_id = a.id
-- LEFT JOIN helpdesk.kb_questions qq ON qq.quiz_id = q.id
-- GROUP BY a.slug ORDER BY a.slug;
""".strip()
    )

    OUT.write_text("\n\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    print("Per slug:", dict(Counter(q["slug"] for q in questions if q["slug"])))


if __name__ == "__main__":
    main()
