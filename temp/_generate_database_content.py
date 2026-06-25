#!/usr/bin/env python3
"""Генерация temp/database-content.txt из HTML прототипов."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "database"
OUT_FILE = ROOT / "database-content.txt"

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    out: list[str] = []
    for ch in text:
        low = ch.lower()
        if low in TRANSLIT:
            out.append(TRANSLIT[low])
        elif ch.isalnum():
            out.append(low)
        elif ch in {" ", "_", "/", "-", "—", "–", "(", ")", "«", "»", ".", ",", "?"}:
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug or "article"


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def sql_json(value: dict) -> str:
    return sql_literal(json.dumps(value, ensure_ascii=False))


def normalize_category(name: str) -> str:
    name = re.sub(r"^\d+\.\s*", "", name.strip())
    return name


def extract_category(html: str) -> str:
    active = re.search(r'<a class="tree-item active"', html)
    if not active:
        return "Прочее"
    before = html[: active.start()]
    folders = re.findall(r'<div class="tree-folder">(.*?)</div>', before)
    if folders:
        return normalize_category(folders[-1])
    return "Прочее"


def extract_title(html: str) -> str:
    m = re.search(r'id="paneArticle"[\s\S]*?<h1>(.*?)</h1>', html)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"<title>База знаний КЦ — (.*?)</title>", html)
    if m:
        return m.group(1).strip()
    return ""


def extract_subtitle(html: str) -> str | None:
    m = re.search(
        r'id="paneArticle"[\s\S]*?<div class="article-title-block"[\s\S]*?'
        r'<div class="da-lbl">(.*?)</div>',
        html,
    )
    if m:
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        return text or None
    return None


def _strip_outer_div_block(html: str, class_name: str) -> str:
    marker = f'<div class="{class_name}">'
    start = html.find(marker)
    if start == -1:
        return html
    pos = start
    depth = 0
    i = start
    while i < len(html):
        if html.startswith("<div", i):
            depth += 1
            i = html.find(">", i) + 1
            continue
        if html.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return (html[:start] + html[i:]).strip()
            continue
        i += 1
    return html


def extract_content_html(html: str) -> str:
    marker = 'id="paneArticle"'
    start = html.find(marker)
    if start == -1:
        return ""
    start = html.find(">", start) + 1
    end = html.find("<!-- ОКНО Б", start)
    if end == -1:
        end = html.find('id="paneQuiz"', start)
    if end == -1:
        return ""
    body = html[start:end]
    return _strip_outer_div_block(body, "article-title-block")


def extract_sidebar_json(html: str) -> dict:
    sidebar: dict = {}
    m = re.search(r'<aside class="sidebar-right">(.*?)</aside>', html, re.DOTALL)
    if not m:
        return sidebar
    aside = m.group(1)

    quick: list[dict[str, str]] = []
    for anchor in re.findall(
        r'<a class="anchor-link"[^>]*href="#([^"]+)"[^>]*>(.*?)</a>',
        aside,
        flags=re.DOTALL,
    ):
        quick.append({
            "anchor": anchor[0].strip(),
            "label": re.sub(r"\s+", " ", anchor[1]).strip(),
        })
    if quick:
        sidebar["quick_access"] = quick

    for card in re.findall(r'<div class="chip-card">(.*?)</div>\s*(?=<div class="chip-card"|</aside>)', aside, re.DOTALL):
        title_m = re.search(r'<div class="chip-title">(.*?)</div>', card, re.DOTALL)
        if not title_m:
            continue
        title = re.sub(r"\s+", " ", title_m.group(1)).strip()
        if title == "Шаблон тикета":
            texts = [
                re.sub(r"\s+", " ", t).strip()
                for t in re.findall(r"<p[^>]*>(.*?)</p>", card, re.DOTALL)
            ]
            sidebar["ticket_template"] = {
                "title": title,
                "lines": [t for t in texts if t],
            }
        elif title == "SLA инженеров":
            pills = []
            for pill in re.findall(r'<div class="pill-item"[^>]*>(.*?)</div>', card, re.DOTALL):
                spans = [
                    re.sub(r"\s+", " ", s).strip()
                    for s in re.findall(r"<span[^>]*>(.*?)</span>", pill, re.DOTALL)
                ]
                if spans:
                    pills.append({"label": spans[0], "value": spans[-1] if len(spans) > 1 else ""})
            sidebar["sla"] = pills
        elif title == "Важное напоминание":
            value_m = re.search(r'class="chip-value"[^>]*>(.*?)</div>', card, re.DOTALL)
            desc_m = re.search(r'class="chip-desc"[^>]*>(.*?)</div>', card, re.DOTALL)
            sidebar["reminder"] = {
                "title": re.sub(r"\s+", " ", value_m.group(1)).strip() if value_m else "",
                "text": re.sub(r"\s+", " ", desc_m.group(1)).strip() if desc_m else "",
            }
    return sidebar


def extract_quiz_data(html: str) -> list[dict]:
    m = re.search(r"const quizData\s*=\s*(\[[\s\S]*?\]);", html)
    if not m:
        return []
    raw = m.group(1)
    for key in ("q", "opts", "ans", "expl"):
        raw = re.sub(rf"\b{key}\s*:", f'"{key}":', raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


def make_summary(content_html: str, title: str) -> str:
    text = re.sub(r"<[^>]+>", " ", content_html)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return title
    return text[:240] + ("…" if len(text) > 240 else "")


def parse_file(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    title = extract_title(html) or path.stem
    category = extract_category(html)
    content_html = extract_content_html(html)
    return {
        "file": path.name,
        "title": title,
        "category": category,
        "subtitle": extract_subtitle(html),
        "slug": slugify(title),
        "summary": make_summary(content_html, title),
        "content_html": content_html,
        "sidebar_json": extract_sidebar_json(html),
        "quiz": extract_quiz_data(html),
    }


def render_sql(articles: list[dict]) -> str:
    categories: dict[str, str] = {}
    for art in articles:
        cat = art["category"]
        if cat not in categories:
            categories[cat] = slugify(cat)

    lines: list[str] = [
        "-- Импорт контента базы знаний из temp/database/*.html",
        "-- Схема: helpdesk",
        "-- Таблицы: kb_categories, kb_articles, kb_quizzes, kb_questions, kb_question_options",
        "--",
        f"-- Статей: {len(articles)}",
        f"-- Разделов: {len(categories)}",
        f"-- Вопросов тестов: {sum(len(a['quiz']) for a in articles)}",
        "--",
        "-- Перед запуском должны быть созданы структуры из temp/learning-db.txt",
        "-- Повторный запуск: раскомментируйте блок очистки внизу или удалите данные вручную.",
        "",
        "BEGIN;",
        "",
        "-- ---------------------------------------------------------------------------",
        "-- Разделы",
        "-- ---------------------------------------------------------------------------",
        "",
    ]

    cat_order = sorted(categories.items(), key=lambda x: x[0])
    for idx, (title, slug) in enumerate(cat_order, start=1):
        lines.append(
            "INSERT INTO helpdesk.kb_categories (parent_id, title, slug, sort_order, is_active)\n"
            f"SELECT NULL, {sql_literal(title)}, {sql_literal(slug)}, {idx * 10}, TRUE\n"
            f"WHERE NOT EXISTS (\n"
            f"    SELECT 1 FROM helpdesk.kb_categories WHERE slug = {sql_literal(slug)}\n"
            ");"
        )

    lines.extend(["", "-- ---------------------------------------------------------------------------", "-- Статьи", "-- ---------------------------------------------------------------------------", ""])

    for art_idx, art in enumerate(articles, start=1):
        cat_slug = categories[art["category"]]
        lines.append(
            f"-- [{art_idx}] {art['file']}\n"
            "INSERT INTO helpdesk.kb_articles (\n"
            "    category_id, title, slug, subtitle, summary, content_html,\n"
            "    content_format, sidebar_json, version, sort_order,\n"
            "    is_published, pass_score_percent, quiz_required, published_at\n"
            ")\n"
            "SELECT\n"
            f"    c.id,\n"
            f"    {sql_literal(art['title'])},\n"
            f"    {sql_literal(art['slug'])},\n"
            f"    {sql_literal(art['subtitle'])},\n"
            f"    {sql_literal(art['summary'])},\n"
            f"    {sql_literal(art['content_html'])},\n"
            "    'html'::helpdesk.kb_content_format,\n"
            f"    {sql_json(art['sidebar_json'])}::jsonb,\n"
            "    1,\n"
            f"    {art_idx * 10},\n"
            "    TRUE,\n"
            "    100,\n"
            "    TRUE,\n"
            "    NOW()\n"
            "FROM helpdesk.kb_categories c\n"
            f"WHERE c.slug = {sql_literal(cat_slug)}\n"
            f"  AND NOT EXISTS (\n"
            f"      SELECT 1 FROM helpdesk.kb_articles WHERE slug = {sql_literal(art['slug'])}\n"
            "  );"
        )
        lines.append("")

    lines.extend(["-- ---------------------------------------------------------------------------", "-- Тесты", "-- ---------------------------------------------------------------------------", ""])

    for art in articles:
        if not art["quiz"]:
            continue
        lines.append(
            f"-- Тест: {art['title']}\n"
            "INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)\n"
            "SELECT\n"
            "    a.id,\n"
            f"    {sql_literal('Проверка знаний темы: ' + art['title'])},\n"
            "    '',\n"
            "    TRUE,\n"
            "    100\n"
            "FROM helpdesk.kb_articles a\n"
            f"WHERE a.slug = {sql_literal(art['slug'])}\n"
            "  AND NOT EXISTS (\n"
            "      SELECT 1 FROM helpdesk.kb_quizzes q2\n"
            "      JOIN helpdesk.kb_articles a2 ON a2.id = q2.article_id\n"
            f"      WHERE a2.slug = {sql_literal(art['slug'])}\n"
            "  );"
        )
        lines.append("")

        for q_idx, question in enumerate(art["quiz"], start=1):
            q_text = question.get("q", "")
            expl = question.get("expl", "")
            opts = question.get("opts", [])
            ans = question.get("ans", 0)
            if isinstance(ans, list):
                correct_indexes = ans
                selection_mode = "multiple"
            else:
                correct_indexes = [ans]
                selection_mode = "single"

            lines.append(
                "INSERT INTO helpdesk.kb_questions (\n"
                "    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags\n"
                ")\n"
                "SELECT\n"
                "    q.id,\n"
                f"    {sql_literal(q_text)},\n"
                f"    {sql_literal(expl)},\n"
                f"    '{selection_mode}'::helpdesk.kb_question_selection_mode,\n"
                f"    {q_idx * 10},\n"
                "    TRUE,\n"
                f"    ARRAY[{sql_literal(art['slug'])}]::text[]\n"
                "FROM helpdesk.kb_quizzes q\n"
                "JOIN helpdesk.kb_articles a ON a.id = q.article_id\n"
                f"WHERE a.slug = {sql_literal(art['slug'])}\n"
                f"  AND NOT EXISTS (\n"
                f"      SELECT 1 FROM helpdesk.kb_questions qq2\n"
                f"      JOIN helpdesk.kb_quizzes q2 ON q2.id = qq2.quiz_id\n"
                f"      JOIN helpdesk.kb_articles a2 ON a2.id = q2.article_id\n"
                f"      WHERE a2.slug = {sql_literal(art['slug'])}\n"
                f"        AND qq2.question_text = {sql_literal(q_text)}\n"
                "  );"
            )

            for opt_idx, opt_text in enumerate(opts):
                is_correct = opt_idx in correct_indexes
                lines.append(
                    "INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)\n"
                    "SELECT\n"
                    "    qq.id,\n"
                    f"    {sql_literal(opt_text)},\n"
                    f"    {'TRUE' if is_correct else 'FALSE'},\n"
                    f"    {opt_idx * 10}\n"
                    "FROM helpdesk.kb_questions qq\n"
                    "JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id\n"
                    "JOIN helpdesk.kb_articles a ON a.id = q.article_id\n"
                    f"WHERE a.slug = {sql_literal(art['slug'])}\n"
                    f"  AND qq.question_text = {sql_literal(q_text)}\n"
                    f"  AND NOT EXISTS (\n"
                    "      SELECT 1 FROM helpdesk.kb_question_options o2\n"
                    "      WHERE o2.question_id = qq.id\n"
                    f"        AND o2.option_text = {sql_literal(opt_text)}\n"
                    "  );"
                )
            lines.append("")

    lines.extend([
        "COMMIT;",
        "",
        "-- ---------------------------------------------------------------------------",
        "-- Очистка перед повторным импортом (раскомментировать при необходимости)",
        "-- ---------------------------------------------------------------------------",
        "-- BEGIN;",
        "-- DELETE FROM helpdesk.kb_question_options;",
        "-- DELETE FROM helpdesk.kb_questions;",
        "-- DELETE FROM helpdesk.kb_quizzes;",
        "-- DELETE FROM helpdesk.kb_articles;",
        "-- DELETE FROM helpdesk.kb_categories;",
        "-- COMMIT;",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    files = sorted(SRC_DIR.glob("*.html"))
    articles = [parse_file(path) for path in files]

    # Уникальные slug при коллизиях
    seen: dict[str, int] = {}
    for art in articles:
        base = art["slug"]
        if base in seen:
            seen[base] += 1
            art["slug"] = f"{base}-{seen[base]}"
        else:
            seen[base] = 1

    sql = render_sql(articles)
    OUT_FILE.write_text(sql, encoding="utf-8")
    legacy = ROOT / "datbase-content.txt"
    legacy.write_text(sql, encoding="utf-8")
    print(f"Wrote {OUT_FILE} ({len(articles)} articles)")
    print(f"Wrote {legacy}")


if __name__ == "__main__":
    main()
