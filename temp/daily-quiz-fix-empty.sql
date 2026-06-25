-- Если SELECT ... WHERE a.slug = 'daily-warmup' возвращает пусто — выполните этот файл.
-- Создаёт: статью daily-warmup → квиз → 1 вопрос (минимум) → политику.

BEGIN;

-- 1. Диагностика (можно выполнить отдельно)
-- SELECT slug FROM helpdesk.kb_categories WHERE is_active LIMIT 10;
-- SELECT slug, is_published FROM helpdesk.kb_articles WHERE slug = 'daily-warmup';
-- SELECT q.id FROM helpdesk.kb_quizzes q JOIN helpdesk.kb_articles a ON a.id = q.article_id WHERE a.slug = 'daily-warmup';

-- 2. Статья (берём spravochnye-materialy или любой активный раздел)
INSERT INTO helpdesk.kb_articles (
    category_id, title, slug, subtitle, summary, content_html,
    content_format, sidebar_json, version, sort_order,
    is_published, pass_score_percent, quiz_required, published_at
)
SELECT
    COALESCE(
        (SELECT id FROM helpdesk.kb_categories WHERE slug = 'spravochnye-materialy' AND is_active LIMIT 1),
        (SELECT id FROM helpdesk.kb_categories WHERE is_active
         ORDER BY helpdesk.kb_categories.sort_order, helpdesk.kb_categories.id LIMIT 1)
    ),
    'Ежедневная разминка',
    'daily-warmup',
    'Служебная запись',
    'Пул вопросов для ежедневного теста.',
    '<div class="section-card"><p>Служебная статья.</p></div>',
    'html'::helpdesk.kb_content_format,
    '{}'::jsonb,
    1, 9999, FALSE, 100, FALSE, NULL
WHERE NOT EXISTS (SELECT 1 FROM helpdesk.kb_articles WHERE slug = 'daily-warmup');

-- Если пусто — нет ни одного раздела kb_categories. Сначала импортируйте temp/datbase-content.txt

-- 3. Квиз
INSERT INTO helpdesk.kb_quizzes (
    article_id, title, description, is_active, passing_score_percent, questions_per_attempt
)
SELECT a.id, 'Ежедневная разминка', 'Тест при входе. Одна попытка в сутки.', TRUE, 100, 5
FROM helpdesk.kb_articles a
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

-- 4. Минимум один вопрос (без вопросов тест не запустить)
INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Турбо-кнопка продлевает срок тарифа абонента?',
    'Нет. Только восстанавливает дневной лимит трафика.',
    'single'::helpdesk.kb_question_selection_mode, 10, TRUE, ARRAY['daily-warmup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_questions qq WHERE qq.quiz_id = q.id);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, только дневной трафик', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.is_correct);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, продлевает тариф', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND NOT o.is_correct);

-- 5. Политика (деактивируем старую активную, если есть)
UPDATE helpdesk.kb_daily_quiz_policies SET is_active = FALSE, updated_at = NOW() WHERE is_active;

INSERT INTO helpdesk.kb_daily_quiz_policies (
    title, is_active, weekdays, timezone, quiz_id,
    questions_per_session, passing_score_percent, is_blocking, allow_skip, require_pass
)
SELECT
    'Ежедневный тест при входе',
    TRUE,
    '{1,2,3,4,5,6,7}'::SMALLINT[],
    'Europe/Moscow',
    q.id,
    5, 100, TRUE, FALSE, FALSE
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup';

COMMIT;

-- Проверка (должна вернуть строку с quiz_id)
SELECT p.id AS policy_id, q.id AS quiz_id, a.slug, a.id AS article_id
FROM helpdesk.kb_daily_quiz_policies p
JOIN helpdesk.kb_quizzes q ON q.id = p.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE p.is_active AND a.slug = 'daily-warmup';
