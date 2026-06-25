-- =============================================================================
-- Ежедневный тест операторов (daily warmup): DDL + начальные данные
-- Запуск: psql "$DATABASE_URL" -f temp/daily-quiz-setup.sql
--
-- Логика:
--   • 1 попытка в сутки (operator_id + session_date, attempt_type = daily_warmup)
--   • Успех (passed) → не показывать до следующего календарного дня
--   • Провал (finished, passed = FALSE) → не показывать до следующего дня
--   • require_pass = FALSE — для «зачёта дня» достаточно завершить попытку
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- ENUM
-- ---------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE helpdesk.kb_daily_quiz_override_mode AS ENUM (
        'inherit',
        'required',
        'exempt'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE helpdesk.kb_daily_quiz_exemption_action AS ENUM (
        'set_inherit',
        'set_required',
        'set_exempt',
        'set_exempt_until'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------------------
-- Таблицы политики и настроек оператора
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS helpdesk.kb_daily_quiz_policies (
    id                      BIGSERIAL PRIMARY KEY,
    title                   TEXT NOT NULL,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    weekdays                SMALLINT[] NOT NULL DEFAULT '{1,2,3,4,5,6,7}'::SMALLINT[],
    timezone                TEXT NOT NULL DEFAULT 'Europe/Moscow',
    show_from_time          TIME NULL,
    show_until_time         TIME NULL,
    quiz_id                 BIGINT NOT NULL
        REFERENCES helpdesk.kb_quizzes (id) ON DELETE RESTRICT,
    questions_per_session   SMALLINT NOT NULL DEFAULT 5,
    passing_score_percent   SMALLINT NOT NULL DEFAULT 100,
    is_blocking             BOOLEAN NOT NULL DEFAULT TRUE,
    allow_skip              BOOLEAN NOT NULL DEFAULT FALSE,
    require_pass            BOOLEAN NOT NULL DEFAULT FALSE,
    valid_from              DATE NULL,
    valid_to                DATE NULL,
    created_by              BIGINT NULL
        REFERENCES users.skystream_users (id) ON DELETE SET NULL,
    updated_by              BIGINT NULL
        REFERENCES users.skystream_users (id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kb_daily_quiz_policies_title_nonempty
        CHECK (length(trim(title)) > 0),
    CONSTRAINT chk_kb_daily_quiz_policies_weekdays_nonempty
        CHECK (cardinality(weekdays) > 0),
    CONSTRAINT chk_kb_daily_quiz_policies_weekdays_range
        CHECK (weekdays <@ ARRAY[1,2,3,4,5,6,7]::SMALLINT[]),
    CONSTRAINT chk_kb_daily_quiz_policies_questions_positive
        CHECK (questions_per_session > 0),
    CONSTRAINT chk_kb_daily_quiz_policies_passing_score
        CHECK (passing_score_percent BETWEEN 0 AND 100),
    CONSTRAINT chk_kb_daily_quiz_policies_time_window
        CHECK (
            show_from_time IS NULL
            OR show_until_time IS NULL
            OR show_from_time < show_until_time
        ),
    CONSTRAINT chk_kb_daily_quiz_policies_valid_range
        CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kb_daily_quiz_policies_one_active
    ON helpdesk.kb_daily_quiz_policies ((TRUE))
    WHERE is_active;

CREATE INDEX IF NOT EXISTS idx_kb_daily_quiz_policies_quiz
    ON helpdesk.kb_daily_quiz_policies (quiz_id);

CREATE TABLE IF NOT EXISTS helpdesk.kb_operator_daily_quiz_settings (
    operator_id             BIGINT PRIMARY KEY
        REFERENCES users.skystream_users (id) ON DELETE CASCADE,
    override_mode           helpdesk.kb_daily_quiz_override_mode NOT NULL DEFAULT 'inherit',
    exempt_until            DATE NULL,
    exempt_reason           TEXT NULL,
    updated_by              BIGINT NULL
        REFERENCES users.skystream_users (id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_operator_daily_quiz_settings_mode
    ON helpdesk.kb_operator_daily_quiz_settings (override_mode);

CREATE INDEX IF NOT EXISTS idx_kb_operator_daily_quiz_settings_exempt_until
    ON helpdesk.kb_operator_daily_quiz_settings (exempt_until)
    WHERE exempt_until IS NOT NULL;

CREATE TABLE IF NOT EXISTS helpdesk.kb_daily_quiz_exemption_log (
    id                      BIGSERIAL PRIMARY KEY,
    operator_id             BIGINT NOT NULL
        REFERENCES users.skystream_users (id) ON DELETE CASCADE,
    action                  helpdesk.kb_daily_quiz_exemption_action NOT NULL,
    override_mode           helpdesk.kb_daily_quiz_override_mode NULL,
    exempt_until            DATE NULL,
    reason                  TEXT NULL,
    changed_by              BIGINT NULL
        REFERENCES users.skystream_users (id) ON DELETE SET NULL,
    changed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_daily_quiz_exemption_log_operator
    ON helpdesk.kb_daily_quiz_exemption_log (operator_id, changed_at DESC);

ALTER TABLE helpdesk.kb_quiz_attempts
    ADD COLUMN IF NOT EXISTS daily_policy_id BIGINT NULL
        REFERENCES helpdesk.kb_daily_quiz_policies (id) ON DELETE SET NULL;

ALTER TABLE helpdesk.kb_quiz_attempts
    ADD COLUMN IF NOT EXISTS daily_policy_snapshot JSONB NULL;

CREATE INDEX IF NOT EXISTS idx_kb_quiz_attempts_daily_policy
    ON helpdesk.kb_quiz_attempts (daily_policy_id, started_at DESC)
    WHERE attempt_type = 'daily_warmup';

-- ---------------------------------------------------------------------------
-- Служебная статья и квиз «Ежедневная разминка»
-- ---------------------------------------------------------------------------

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
    'Пул вопросов для ежедневного теста операторов. Не отображается в списке /kb.',
    '<div class="section-card"><p>Служебная статья для ежедневного тестирования операторов.</p></div>',
    'html'::helpdesk.kb_content_format,
    '{}'::jsonb,
    1,
    9999,
    FALSE,
    100,
    FALSE,
    NULL
WHERE NOT EXISTS (SELECT 1 FROM helpdesk.kb_articles WHERE slug = 'daily-warmup');

INSERT INTO helpdesk.kb_quizzes (
    article_id, title, description, is_active, passing_score_percent, questions_per_attempt
)
SELECT
    a.id,
    'Ежедневная разминка',
    'Короткий тест при входе на портал. Одна попытка в сутки.',
    TRUE,
    100,
    5
FROM helpdesk.kb_articles a
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

-- ---------------------------------------------------------------------------
-- Вопросы пула (5 штук для старта)
-- ---------------------------------------------------------------------------

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Абонент видит списание с карты и не понимает за что. Первый шаг оператора?',
    'Запросить чек/выписку и проверить операцию в системе.',
    'single'::helpdesk.kb_question_selection_mode, 10, TRUE, ARRAY['daily-warmup', 'oplata']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id
        AND qq.question_text LIKE 'Абонент видит списание с карты%'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить чек и проверить в системе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text LIKE 'Абонент видит списание с карты%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 10);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу оформить возврат в бухгалтерию', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text LIKE 'Абонент видит списание с карты%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 0);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Турбо-кнопка продлевает тариф абонента?',
    'Нет. Турбо восстанавливает только дневной лимит трафика.',
    'single'::helpdesk.kb_question_selection_mode, 20, TRUE, ARRAY['daily-warmup', 'tarify']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text LIKE 'Турбо-кнопка продлевает%'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, только восстанавливает дневной трафик', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Турбо-кнопка продлевает%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.is_correct);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, продлевает срок тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Турбо-кнопка продлевает%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 0);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Абонент не может войти в личный кабинет. Что проверить в первую очередь?',
    'Логин (email/договор) и возможность сброса пароля.',
    'single'::helpdesk.kb_question_selection_mode, 30, TRUE, ARRAY['daily-warmup', 'lk']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text LIKE 'Абонент не может войти%'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Логин и пароль, предложить сброс', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Абонент не может войти%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.is_correct);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу создать заявку инженерам', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Абонент не может войти%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 0);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Платёж абонента через СБП не зачислился. Какой срок ожидания сообщить?',
    'До 24 часов для СБП.',
    'single'::helpdesk.kb_question_selection_mode, 40, TRUE, ARRAY['daily-warmup', 'oplata']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text LIKE 'Платёж абонента через СБП%'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 24 часов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Платёж абонента через СБП%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.is_correct);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно, иначе ошибка', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Платёж абонента через СБП%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 0);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id,
    'Нет интернета у абонента. В каком порядке действовать?',
    'Баланс → станция → роутер → заявка инженерам.',
    'single'::helpdesk.kb_question_selection_mode, 50, TRUE, ARRAY['daily-warmup', 'diagnostika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text LIKE 'Нет интернета у абонента%'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Баланс, станция, роутер, затем заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Нет интернета у абонента%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.is_correct);

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу передать инженерам', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.question_text LIKE 'Нет интернета у абонента%'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_question_options o WHERE o.question_id = qq.id AND o.sort_order = 0);

-- ---------------------------------------------------------------------------
-- Активная политика: каждый день, 5 вопросов, 1 попытка в сутки
-- require_pass = FALSE → после finished (даже с ошибками) до завтра не показывать
-- ---------------------------------------------------------------------------

UPDATE helpdesk.kb_daily_quiz_policies
SET is_active = FALSE, updated_at = NOW()
WHERE is_active;

INSERT INTO helpdesk.kb_daily_quiz_policies (
    title,
    is_active,
    weekdays,
    timezone,
    show_from_time,
    show_until_time,
    quiz_id,
    questions_per_session,
    passing_score_percent,
    is_blocking,
    allow_skip,
    require_pass
)
SELECT
    'Ежедневный тест при входе',
    TRUE,
    '{1,2,3,4,5,6,7}'::SMALLINT[],
    'Europe/Moscow',
    NULL,
    NULL,
    q.id,
    5,
    100,
    TRUE,
    FALSE,
    FALSE
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_daily_quiz_policies p WHERE p.is_active
  );

COMMIT;

-- Проверка
SELECT p.id, p.title, p.weekdays, p.questions_per_session, p.require_pass, q.id AS quiz_id, a.slug
FROM helpdesk.kb_daily_quiz_policies p
JOIN helpdesk.kb_quizzes q ON q.id = p.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE p.is_active;

SELECT COUNT(*) AS question_count
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup' AND qq.is_active;
