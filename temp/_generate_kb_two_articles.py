"""Генерирует temp/kb-two-articles.sql из HTML-прототипов двух статей БЗ.

Запуск: python3 temp/_generate_kb_two_articles.py
Скрипт идемпотентен: статья с тем же slug удаляется (каскадом вместе с тестом) и создаётся заново.
"""
import json
import re
import subprocess
from html import unescape
from pathlib import Path

TEMP = Path(__file__).parent

ARTICLES = [
    {
        "src": "БЗ_КЦ_IP_подключения_vs_страница_авторизации (6).html",
        "slug": "ip-podklyucheniya-vs-stranitsa-avtorizatsii",
        "category": "podklyuchenie-i-internet",
        "sort_order": 270,
        "images": ["hotspot-ip-chat-example", "hotspot-ip-session-log", "hotspot-ip-user-card"],
        "quick_access": [
            {"label": "Суть проблемы", "anchor": "sec-intro"},
            {"label": "Пример ошибки", "anchor": "sec-case"},
            {"label": "Где смотреть каждый IP", "anchor": "sec-where"},
            {"label": "Какой за что отвечает", "anchor": "sec-diff"},
        ],
    },
    {
        "src": "БЗ_КЦ_Долгое_удержание_на_линии (2).html",
        "slug": "dolgoe-uderzhanie-na-linii",
        "category": "rabota-s-abonentami",
        "sort_order": 280,
        "images": [],
        "quick_access": [
            {"label": "Суть проблемы", "anchor": "sec-intro"},
            {"label": "Почему это происходит", "anchor": "sec-why"},
            {"label": "Как делать правильно", "anchor": "sec-howto"},
        ],
        "extra_before_rule": (
            '<div class="pl-info"><strong>Ориентиры по времени:</strong><br>'
            "● Возвращайтесь к диалогу <strong>каждые 45-60 секунд</strong>: сообщите этап, задайте вопрос или назовите срок.<br>"
            "● Зона риска — <strong>5-7 минут</strong> суммарного удержания на линии: у абонента появляется ощущение покинутости.</div>\n                "
        ),
    },
]


def q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def build(cfg: dict) -> str:
    s = (TEMP / cfg["src"]).read_text(encoding="utf-8")
    title = plain(re.search(r"<h1>(.*?)</h1>", s, re.S).group(1))
    subtitle = plain(re.search(r"<h1>.*?</h1>\s*<p>(.*?)</p>", s, re.S).group(1))

    # тело статьи: от первого section-card до кнопки «Пройти тестирование»
    start = s.index('<div class="section-card"')
    end = s.index('<div style="text-align: center; border-top', start)
    body = s[start:end].rstrip()
    body = re.sub(r"<!--.*?-->\s*", "", body, flags=re.S)

    imgs = iter(cfg["images"])
    body = re.sub(
        r'<img src="data:image/jpeg;base64,[^"]+" alt="([^"]*)">',
        lambda m: f'<img src="/static/images/kb/{next(imgs)}.webp" alt="{m.group(1)}" loading="lazy" />',
        body,
    )
    body = body.replace('<div class="ip">', '<div class="card-ip__val">')
    # «пошаговые» блоки прототипа -> check-card-*
    body = (
        body.replace("steps-list", "check-card-list")
        .replace("step-row", "check-card-item")
        .replace("step-icon", "check-card-icon")
        .replace("step-text", "check-card-text")
    )
    extra = cfg.get("extra_before_rule")
    if extra:
        body = body.replace('<div class="rule">', extra + '<div class="rule">', 1)
    # убираем лишние отступы прототипа (4 пробела вложенности)
    body = "\n".join(l[12:] if l.startswith(" " * 12) else l for l in body.split("\n"))
    assert "data:image" not in body

    plain_body = plain(body)
    summary = f"{subtitle} {plain_body}"[:300]

    node = (
        "const fs=require('fs');const s=fs.readFileSync(process.argv[1],'utf8');"
        "const m=s.match(/const quizData = (\\[[\\s\\S]*?\\]);\\s*let state/);"
        "console.log(JSON.stringify(eval(m[1])));"
    )
    quiz = json.loads(subprocess.check_output(["node", "-e", node, str(TEMP / cfg["src"])]))
    assert len(quiz) == 5

    slug = cfg["slug"]
    sidebar = json.dumps({"quick_access": cfg["quick_access"]}, ensure_ascii=False)
    out = [f"-- {title}", f"DELETE FROM helpdesk.kb_articles WHERE slug = {q(slug)};"]
    out.append(
        "INSERT INTO helpdesk.kb_articles (category_id, title, slug, subtitle, summary, content_html, sidebar_json,"
        " sort_order, is_published, pass_score_percent, quiz_required, published_at)\n"
        f"SELECT c.id, {q(title)}, {q(slug)}, {q(subtitle)}, {q(summary)},\n{q(body)},\n{q(sidebar)}::jsonb,"
        f" {cfg['sort_order']}, TRUE, 100, TRUE, NOW()\n"
        f"FROM helpdesk.kb_categories c WHERE c.slug = {q(cfg['category'])};"
    )
    out.append(
        "INSERT INTO helpdesk.kb_quizzes (article_id, title, passing_score_percent)\n"
        f"SELECT a.id, {q('Проверка знаний темы: ' + title)}, 100 FROM helpdesk.kb_articles a WHERE a.slug = {q(slug)};"
    )
    for i, item in enumerate(quiz, 1):
        out.append(
            "WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)\n"
            f"  SELECT z.id, {q(item['q'])}, {q(item['expl'])}, 'single', {i * 10}, ARRAY[{q(slug)}]\n"
            f"  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = {q(slug)} RETURNING id)\n"
            "INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)\nSELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES\n"
            + ",\n".join(
                f"  ({q(o)}, {'TRUE' if j == item['ans'] else 'FALSE'}, {j * 10})" for j, o in enumerate(item["opts"])
            )
            + "\n) AS v(t, c, o);"
        )
    return "\n".join(out)


sql = "BEGIN;\n\n" + "\n\n".join(build(c) for c in ARTICLES) + "\n\nCOMMIT;\n"
(TEMP / "kb-two-articles.sql").write_text(sql, encoding="utf-8")
print("ok", len(sql))
