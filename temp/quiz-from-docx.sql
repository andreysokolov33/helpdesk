-- =============================================================================

-- Квизы из: temp/database/Тестирование (список всех вопросов).docx

-- Вопросов: 171 | Тем: 19 | Статей: 23 + daily-warmup

-- Сгенерировано: temp/_generate_quiz_from_docx.py

--

-- Если ошибка 25P02 (transaction aborted): выполните ROLLBACK; и запустите снова.

-- =============================================================================



-- Сброс прерванной транзакции в текущей сессии (безопасно, если транзакции нет)

ROLLBACK;



BEGIN;



-- Очистка перед переимпортом: попытки ссылаются на вопросы (RESTRICT)

UPDATE helpdesk.kb_article_progress p
SET last_attempt_id = NULL, updated_at = NOW()
WHERE p.last_attempt_id IN (
    SELECT qa.id
    FROM helpdesk.kb_quiz_attempts qa
    JOIN helpdesk.kb_articles a ON a.id = qa.article_id
    WHERE a.slug IN ('daily-warmup', 'finansovye-voprosy-i-dokumenty', 'glossariy-terminov', 'kak-otrabatyvat-zhaloby', 'kak-sobrat-dannye-dlya-zayavki', 'kuda-uhodit-trafik', 'lichnyy-kabinet-i-dostup', 'lineyki-tarifov', 'mediakontent-videoservis-multikast', 'net-podklyucheniya-k-internetu', 'novye-podklyucheniya', 'oplatil-no-dengi-ne-prishli', 'organizatsionnye-voprosy', 'problemy-s-oborudovaniem', 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov', 'rkn-blokirovki-i-ogranicheniya-dostupa', 'smena-tarifa', 'sroki-otveta-inzhenerov', 'sutochnyy-sbros-obnovlenie-trafika', 'trebovanie-vozvrata-deneg', 'turbo-knopka', 'voprosy-po-spisaniyam-i-rashodam', 'vosstanovlenie-trafika', 'zamorozka-razmorozka-tarifa')
);

DELETE FROM helpdesk.kb_quiz_attempts qa
USING helpdesk.kb_articles a
WHERE qa.article_id = a.id
  AND a.slug IN ('daily-warmup', 'finansovye-voprosy-i-dokumenty', 'glossariy-terminov', 'kak-otrabatyvat-zhaloby', 'kak-sobrat-dannye-dlya-zayavki', 'kuda-uhodit-trafik', 'lichnyy-kabinet-i-dostup', 'lineyki-tarifov', 'mediakontent-videoservis-multikast', 'net-podklyucheniya-k-internetu', 'novye-podklyucheniya', 'oplatil-no-dengi-ne-prishli', 'organizatsionnye-voprosy', 'problemy-s-oborudovaniem', 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov', 'rkn-blokirovki-i-ogranicheniya-dostupa', 'smena-tarifa', 'sroki-otveta-inzhenerov', 'sutochnyy-sbros-obnovlenie-trafika', 'trebovanie-vozvrata-deneg', 'turbo-knopka', 'voprosy-po-spisaniyam-i-rashodam', 'vosstanovlenie-trafika', 'zamorozka-razmorozka-tarifa');

-- Ответы на вопросы удаляются каскадом с попытками; варианты — с вопросами

DELETE FROM helpdesk.kb_questions qq
USING helpdesk.kb_quizzes q, helpdesk.kb_articles a
WHERE qq.quiz_id = q.id
  AND q.article_id = a.id
  AND a.slug IN ('daily-warmup', 'finansovye-voprosy-i-dokumenty', 'glossariy-terminov', 'kak-otrabatyvat-zhaloby', 'kak-sobrat-dannye-dlya-zayavki', 'kuda-uhodit-trafik', 'lichnyy-kabinet-i-dostup', 'lineyki-tarifov', 'mediakontent-videoservis-multikast', 'net-podklyucheniya-k-internetu', 'novye-podklyucheniya', 'oplatil-no-dengi-ne-prishli', 'organizatsionnye-voprosy', 'problemy-s-oborudovaniem', 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov', 'rkn-blokirovki-i-ogranicheniya-dostupa', 'smena-tarifa', 'sroki-otveta-inzhenerov', 'sutochnyy-sbros-obnovlenie-trafika', 'trebovanie-vozvrata-deneg', 'turbo-knopka', 'voprosy-po-spisaniyam-i-rashodam', 'vosstanovlenie-trafika', 'zamorozka-razmorozka-tarifa');



-- Служебная статья и квиз для ежедневного теста (если ещё нет)

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

-- Квиз: Ежедневная разминка

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Ежедневная разминка', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);



-- -----------------------------------------------------------------------------

-- Вопросы по статьям /kb (по темам)

-- -----------------------------------------------------------------------------



-- Квиз: Финансовые вопросы и документы

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Финансовые вопросы и документы', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?', 'ЮЛ и партнёры — к менеджеру. Контакты: cm@wifitochka.ru, 8:00–16:00 МСК.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, где в ЛК посмотреть', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, где в ЛК посмотреть'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Направить к менеджеру по работе с клиентами и партнёрами', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Направить к менеджеру по работе с клиентами и партнёрами'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?', 'Оператор не принимает финансовых решений. Возвраты делают только инженеры через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор контакт-центра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор контакт-центра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:', 'Менеджер работает с 8:00 до 16:00 по Москве в будни.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '9:00–18:00 МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '9:00–18:00 МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8:00–16:00 МСК', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8:00–16:00 МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Круглосуточно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Круглосуточно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:', 'Оператор фиксирует запрос и передаёт. Документы готовят инженеры или менеджер.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Распечатать и отправить документы', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Распечатать и отправить документы'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Корректно зафиксировать обращение и передать', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Корректно зафиксировать обращение и передать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что документы не предоставляются', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что документы не предоставляются'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?', 'Оператор не возвращает деньги. Только заявка, решение принимает инженер.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что возврат невозможен', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что возврат невозможен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на компенсацию с ID, периодом и причиной', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на компенсацию с ID, периодом и причиной'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно через систему', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно через систему'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:', 'Проверяем историю (видно подключение и отключение). Если случайно — заявка на возврат.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что это его проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что это его проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить историю операций и создать заявку на возврат', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить историю операций и создать заявку на возврат'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключить тариф обратно самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключить тариф обратно самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):', 'Вывод на карту — по решению инженеров через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это делает оператор через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это делает оператор через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: вывод на карту возможен по решению инженеров, создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: вывод на карту возможен по решению инженеров, создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что вывод только на баланс', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'finansovye-voprosy-i-dokumenty'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что вывод только на баланс'
  );



-- Квиз: Глоссарий и термины

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Глоссарий и термины', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое MAC-адрес?MAC-адрес?', 'MAC-адрес — уникальный идентификатор сетевого устройства, 12 символов.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Физический адрес устройства (роутера, телефона) — 12 символов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Физический адрес устройства (роутера, телефона) — 12 символов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Модель роутера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Модель роутера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?', 'Принципиально разные типы подключения. HOTSPOT — ввод данных в браузере. PPPoE — в настройках роутера.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только названием, это одно и то же', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только названием, это одно и то же'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT — через браузер, сессия активна пока устройство онлайн. PPPoE — «зашит» в роутер, сессия всегда активна', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT — через браузер, сессия активна пока устройство онлайн. PPPoE — «зашит» в роутер, сессия всегда активна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT быстрее', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT быстрее'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое «лимит сессий»?', 'Лимит сессий — это ограничение на количество одновременно подключённых устройств.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое «лимит сессий»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальная скорость интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальная скорость интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальное количество устройств, которые могут быть онлайн одновременно', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальное количество устройств, которые могут быть онлайн одновременно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальный расход трафика', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальный расход трафика'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда снимается ограничение скорости?', 'Скорость восстанавливается после сброса трафика или Турбо-кнопки.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда снимается ограничение скорости?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'После суточного сброса или подключения Турбо-кнопки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'После суточного сброса или подключения Турбо-кнопки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'При перезагрузке роутера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'При перезагрузке роутера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое ID абонента?ID абонента?', 'ID — уникальный номер учётной записи. Он же логин для входа в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пароль от ЛК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пароль от ЛК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Уникальный номер учётной записи, логин для входа', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Уникальный номер учётной записи, логин для входа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для чего нужна кнопка «Диагностика»?', 'Диагностика проверяет: учётная запись, тариф, баланс, станция, сессия, лимит.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для создания заявки', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для создания заявки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для проверки 6 параметров учётной записи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для проверки 6 параметров учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для отправки уведомления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для отправки уведомления'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?', 'PPPoE — настройки прописаны в роутере, подключается автоматически.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'PPPoE', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'PPPoE'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'VPN', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'glossariy-terminov'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'VPN'
  );



-- Квиз: Как отрабатывать жалобы

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Как отрабатывать жалобы', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?', 'Первое правило работы с жалобой — не принимать на свой счёт и не защищаться. Признать эмоции абонента и перевести в конструктив.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что вы не виноваты, и перечислить причины', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что вы не виноваты, и перечислить причины'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не защищаться и признать: «Понимаю ваше недовольство, давайте разберёмся»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не защищаться и признать: «Понимаю ваше недовольство, давайте разберёмся»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что надо подождать и переключить на инженера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что надо подождать и переключить на инженера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент требует: «Соедините с руководителем!». Как реагировать?', 'Отказывать в соединении с руководителем нельзя. Но номер телефона не даём — только передаём запрос.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что руководитель занят, и попросить подождать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что руководитель занят, и попросить подождать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не отказывать. Спокойно ответить: «Я передам ваш запрос, с вами свяжутся»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не отказывать. Спокойно ответить: «Я передам ваш запрос, с вами свяжутся»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Дать номер телефона руководителя', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Дать номер телефона руководителя'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза лучше всего снижает напряжение?', 'Фраза «я понимаю» снимает половину напряжения. Шаблонные фразы («ваше мнение важно для нас») звучат как насмешка.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ваше мнение важно для нас»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ваше мнение важно для нас»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы не правы, давайте посмотрим факты»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы не правы, давайте посмотрим факты»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я понимаю, это неприятно. Давайте посмотрим, что можно сделать»', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я понимаю, это неприятно. Давайте посмотрим, что можно сделать»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?', 'Нужно найти историю, извиниться за ожидание и дать конкретный срок решения.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить историю обращений и извиниться за ожидание', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить историю обращений и извиниться за ожидание'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что надо подождать, заявка уже есть', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что надо подождать, заявка уже есть'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую заявку с нуля', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую заявку с нуля'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Чего НЕЛЬЗЯ делать при работе с жалобой?', 'Перебивать и спорить нельзя. Признавать проблему и давать срок — можно и нужно.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Признавать проблему и извиняться', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Признавать проблему и извиняться'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перебивать абонента и спорить с ним', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перебивать абонента и спорить с ним'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Давать конкретный срок решения', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Давать конкретный срок решения'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза НЕ годится для работы с жалобой?', 'Фраза «это не в моих обязанностях» вызывает раздражение. Лучше: «Я передам ваш вопрос специалисту»',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я понимаю ваше недовольство»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я понимаю ваше недовольство»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это не входит в мои обязанности»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это не входит в мои обязанности»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Давайте посмотрим, что показывает система»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?', 'На недоверие нельзя обижаться. Объяснять просто и по делу, без шаблонных фраз.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доказать, что он не прав, привести факты', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доказать, что он не прав, привести факты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не обижаться. Объяснять просто без шаблонов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не обижаться. Объяснять просто без шаблонов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Передать заявку инженерам', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Передать заявку инженерам'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Главное правило работы с жалобой — это:', 'Жалоба — это сигнал о проблеме. Абонент злится на ситуацию, не на вас лично.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Главное правило работы с жалобой — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Как можно быстрее завершить диалог', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Как можно быстрее завершить диалог'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Жалоба — это не нападение, а сигнал', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Жалоба — это не нападение, а сигнал'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всегда предлагать компенсацию', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всегда предлагать компенсацию'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Вместо «Ожидайте» лучше сказать:', 'Конкретный срок снимает тревожность. «Скоро» — худший вариант, абонент не знает, сколько ждать.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Скоро всё сделаем»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Скоро всё сделаем»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ориентировочно до [срок], я прослежу, и вернусь к вам с обратной связью»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ориентировочно до [срок], я прослежу, и вернусь к вам с обратной связью»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вам перезвонят»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вам перезвонят»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делать в первые 30 секунд разговора с разгневанным абонентом?', 'Первые 30 секунд абонент сбрасывает эмоции. В это время бесполезно что-то объяснять.',
       'single'::helpdesk.kb_question_selection_mode, 100, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Начинать диагностику', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Начинать диагностику'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Дать выговориться, не перебивать', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Дать выговориться, не перебивать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу извиниться за всё', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу извиниться за всё'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза-помощник правильная?', 'Фраза «вы не правы» удваивает напряжение. Нужно без обвинения переводить в конструктив.',
       'single'::helpdesk.kb_question_selection_mode, 110, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза-помощник правильная?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы не правы, давайте посмотрим, что показывает система»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы не правы, давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Давайте посмотрим, что показывает система»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы ошибаетесь, проверьте ещё раз»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы ошибаетесь, проверьте ещё раз»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Лучший способ перевести абонента из эмоций в конструктив:', 'Конкретное действие переключает внимание абонента с эмоций на решение.',
       'single'::helpdesk.kb_question_selection_mode, 120, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать «успокойтесь»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать «успокойтесь»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить конкретное действие: «Давайте я проверю по вашей учётной записи»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить конкретное действие: «Давайте я проверю по вашей учётной записи»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать всё вернуть', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-otrabatyvat-zhaloby'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать всё вернуть'
  );



-- Квиз: Дополнительные ситуации

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Дополнительные ситуации', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»', 'Сначала уточнить — все устройства или одно. Если все — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это нормально', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это нормально'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить: одно устройство или все? Если одно — проблема устройства. Если все — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить: одно устройство или все? Если одно — проблема устройства. Если все — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не знает свой логин для входа. Что делать?', 'Логин (ID) виден в карточке абонента.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую учётную запись', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую учётную запись'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в карточке (ID) и сообщить', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в карточке (ID) и сообщить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбросить ЛК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбросить ЛК'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Диагностика показывает: «Лимит сессий превышен». Что делать?', 'Лимит сессий можно сбросить в ЛК или помочь и сбросить в системе',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего, это проблема абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего, это проблема абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что превышен лимит устройств. Попросить сбросить сессии в ЛК или помочь и сбросить их в системе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что превышен лимит устройств. Попросить сбросить сессии в ЛК или помочь и сбросить их в системе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?', 'Замедление конкретных ресурсов — не техническая проблема, а блокировка РКН.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это проблема вашего интернета»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это проблема вашего интернета»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Возможно, замедление/блокировка РКН. Мы не можем на это повлиять»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Возможно, замедление/блокировка РКН. Мы не можем на это повлиять»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку инженерам»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку инженерам»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:', 'Мы не знаем и не можем комментировать сроки снятия блокировок РКН.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Завтра»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Завтра»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это решается на государственном уровне, у нас нет такой информации»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это решается на государственном уровне, у нас нет такой информации»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Через неделю»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Через неделю»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое «сессия» простыми словами?', 'Сессия — это подключение устройства к сети. Одно устройство = одна сессия.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое «сессия» простыми словами?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Время работы интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Время работы интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключение одного устройства к сети', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключение одного устройства к сети'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость интернета', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость интернета'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:', 'Не сравнивать тарифы абонентов. Перенаправить к информации на сайте/в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«У всех такие же»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«У всех такие же»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Цены можно посмотреть на сайте и в ЛК. Если у вас есть вопросы по тарифу — я могу помочь»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Цены можно посмотреть на сайте и в ЛК. Если у вас есть вопросы по тарифу — я могу помочь»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это секретная информация»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это секретная информация»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент кричит и оскорбляет оператора. Ваше действие?', 'Не принимать на свой счёт. ────────────────────────────────────────────────────────────────────────────────',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответить тем же', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответить тем же'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Спокойно выслушать, не принимать на свой счёт.', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Спокойно выслушать, не принимать на свой счёт.'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Положить трубку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Положить трубку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как лучше начать диалог с раздражённым абонентом?', 'Сразу переводить в конструктив — предложить конкретное действие.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Слушаю вас, чем могу помочь?»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Слушаю вас, чем могу помочь?»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Здравствуйте! Давайте я проверю по вашей учётной записи, что можно сделать»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Здравствуйте! Давайте я проверю по вашей учётной записи, что можно сделать»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Не волнуйтесь, сейчас всё решим»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Не волнуйтесь, сейчас всё решим»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:', 'Заявка на добавление контента. Решение за инженерами.',
       'single'::helpdesk.kb_question_selection_mode, 100, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я передам запрос инженерам» — заявка с названием контента', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я передам запрос инженерам» — заявка с названием контента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Фильмы загружаются автоматически»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Фильмы загружаются автоматически»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ищите в других сервисах»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ищите в других сервисах»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как часто обновляется контент на Мультикасте?Мультикасте?', 'Оператор не управляет контентом Мультикаста. Вопросы по контенту — в заявку.',
       'single'::helpdesk.kb_question_selection_mode, 110, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Каждый день', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Каждый день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Эту информацию оператор не знает. Запрос на обновление — через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Эту информацию оператор не знает. Запрос на обновление — через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Раз в неделю', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Раз в неделю'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?', 'Ситуация 2 — «Не было доступа к сети»',
       'single'::helpdesk.kb_question_selection_mode, 120, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это неизрасходованный трафик — инженеры проверят остаток и восстановят', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это неизрасходованный трафик — инженеры проверят остаток и восстановят'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это «не было доступа к сети» — уточнить даты, создать заявку инженерам. Они проверят расход трафика за эти дни и, если его не было, продлят тариф', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это «не было доступа к сети» — уточнить даты, создать заявку инженерам. Они проверят расход трафика за эти дни и, если его не было, продлят тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это автопродление — создать заявку на возврат средств', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это автопродление — создать заявку на возврат средств'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?', 'Раздел «Когда ждать ответа от инженеров» — после 16:00 до следующего рабочего дня',
       'single'::helpdesk.kb_question_selection_mode, 130, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«В течение 15 минут» — это рабочее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«В течение 15 минут» — это рабочее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Инженеры ответят в течение 8 часов»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Инженеры ответят в течение 8 часов»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Уже вечер пятницы, поэтому заявку рассмотрят в начале следующей рабочей недели»', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Уже вечер пятницы, поэтому заявку рассмотрят в начале следующей рабочей недели»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?', 'Ситуация 2. Сначала чек и проверка в системе.',
       'single'::helpdesk.kb_question_selection_mode, 140, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на возврат в бухгалтерию', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на возврат в бухгалтерию'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот чека, проверить в системе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот чека, проверить в системе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать - ошибка банка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать - ошибка банка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Пополнил на 1000, на счету 150. Что могло произойти?', 'Ситуация 1. Автопродление - главная причина. Либо домочадцы.',
       'single'::helpdesk.kb_question_selection_mode, 150, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ошибка - срочная заявка', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ошибка - срочная заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить активно ли автопродление', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить активно ли автопродление'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Комиссия банка 850', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Комиссия банка 850'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?', 'Раздел «Когда ждать ответа от инженеров». С 8:00 до 16:00 в будни по МСК - 15 минут. Остальное время, выходные и праздники - до следующего рабочего дня. 17:30 пятницы - уже не рабочее время.',
       'single'::helpdesk.kb_question_selection_mode, 160, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В течение 15 минут - это рабочее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В течение 15 минут - это рабочее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В течение часа', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В течение часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующей рабочей недели (после 16:00 в будни - до следующего рабочего дня)', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующей рабочей недели (после 16:00 в будни - до следующего рабочего дня)'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?', 'Ситуация 1 - количество сбросов = количество дней минус 1. Первый пакет даётся при подключении, дальше каждый день - по одному сбросу. 7 дней = 6 сбросов + первый пакет при подключении.',
       'single'::helpdesk.kb_question_selection_mode, 170, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '7 раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '7 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '6 раз', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '6 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8 раз', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8 раз'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В каких случаях оператор должен создать заявку инженерам?', 'Общий принцип из памятки: «если у абонента остались вопросы и доводы КЦ не работают - оператор создаёт заявку инженерам». Также заявка обязательна при смене времени сброса.',
       'single'::helpdesk.kb_question_selection_mode, 180, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент спрашивает время сброса', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент спрашивает время сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент жалуется на быстрый расход трафика', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент жалуется на быстрый расход трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если у абонента остались вопросы и доводы КЦ не работают, или если требуется изменить время сброса', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если у абонента остались вопросы и доводы КЦ не работают, или если требуется изменить время сброса'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 190, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продление тарифа на новый срок', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продление тарифа на новый срок'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Платная опция, которая восстанавливает суточный лимит трафика на безлимитных тарифах, также восстанавливает скорость из ограничения скорости до скорости по тарифу', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Платная опция, которая восстанавливает суточный лимит трафика на безлимитных тарифах, также восстанавливает скорость из ограничения скорости до скорости по тарифу'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Смена тарифа на слайдер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Смена тарифа на слайдер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько стоит турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 200, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа — от 50 до 300 ₽', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа — от 50 до 300 ₽'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '160 ₽ — фиксированная цена Зависит от объёма суточного пакета трафика, например цена турбо-кнопки для тарифа Безлимитный 300 стоит 180р., а для тарифа Безлимитный 1500 стоит 540р.. Уточню, что стоимость турбок-нопки это стоимость суточного тариф с таким же объёмом трафика, например турбо-кнопка для тарифа Безлимитный 300 на 30 суток стоит 180р. как и тариф Безлимитный 300 на 1 день', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '160 ₽ — фиксированная цена Зависит от объёма суточного пакета трафика, например цена турбо-кнопки для тарифа Безлимитный 300 стоит 180р., а для тарифа Безлимитный 1500 стоит 540р.. Уточню, что стоимость турбок-нопки это стоимость суточного тариф с таким же объёмом трафика, например турбо-кнопка для тарифа Безлимитный 300 на 30 суток стоит 180р. как и тариф Безлимитный 300 на 1 день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '100 ₽', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '100 ₽'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'На каких тарифах доступна турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 210, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только на безлимитных тарифах', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только на безлимитных тарифах'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На всех тарифах, включая слайдер', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На всех тарифах, включая слайдер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только на слайдер-тарифах', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только на слайдер-тарифах'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делает турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 220, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делает турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продлевает тариф на 24 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продлевает тариф на 24 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Восстанавливает суточный лимит трафика, который выбрал абонент, также восстанавливает скорость из ограничения скорости до скорости по тарифу', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Восстанавливает суточный лимит трафика, который выбрал абонент, также восстанавливает скорость из ограничения скорости до скорости по тарифу'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Добавляет 500 МБ трафика независимо от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Добавляет 500 МБ трафика независимо от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?', '',
       'single'::helpdesk.kb_question_selection_mode, 230, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что это техническое ограничение системы', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что это техническое ограничение системы'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Чтобы абонент не платил, когда трафик ещё есть — защита от лишних трат', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Чтобы абонент не платил, когда трафик ещё есть — защита от лишних трат'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что кнопка активируется только раз в сутки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что кнопка активируется только раз в сутки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопка продлевает тариф?', '',
       'single'::helpdesk.kb_question_selection_mode, 240, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, на 24 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, на 24 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, до конца месяца', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, до конца месяца'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, она только восстанавливает дневной лимит, но не продлевает тариф', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, она только восстанавливает дневной лимит, но не продлевает тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 250, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что турбо-кнопка бесплатна', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что турбо-кнопка бесплатна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что турбо-кнопка не продлевает тариф, а только восстанавливает дневной лимит', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что турбо-кнопка не продлевает тариф, а только восстанавливает дневной лимит'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что после подключения тариф автоматически продлится', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что после подключения тариф автоматически продлится'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 260, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик турбо-кнопки сохранится до следующего подключения тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик турбо-кнопки сохранится до следующего подключения тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик турбо-кнопки сгорит вместе с тарифом. Инженеры могут компенсировать стоимость', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик турбо-кнопки сгорит вместе с тарифом. Инженеры могут компенсировать стоимость'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги автоматически вернутся на баланс', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги автоматически вернутся на баланс'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 270, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента, скриншот чека и адрес', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента, скриншот чека и адрес'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента с пометкой о компенсации', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента с пометкой о компенсации'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только название тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только название тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В каких случаях применяется турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 280, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф активен, трафик закончился, остаток пакета меньше 80 %', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф активен, трафик закончился, остаток пакета меньше 80 %'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф закончился, нужно продлить', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф закончился, нужно продлить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент хочет сменить тариф на другой', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kak-sobrat-dannye-dlya-zayavki'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент хочет сменить тариф на другой'
  );



-- Квиз: Дополнительные ситуации

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Дополнительные ситуации', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?', 'Самая частая причина — автообновления приложений и ОС, синхронизация облака.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Кто-то украл пароль', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Кто-то украл пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Фоновые обновления приложений', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Фоновые обновления приложений'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбой системы', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбой системы'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как помочь абоненту проверить, куда уходит трафик?', 'Мы не видим, на какие приложения тратится трафик. Только на устройстве или через GlassWire.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть на нашей стороне', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть на нашей стороне'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Порекомендовать установить GlassWire или проверить «Передачу данных» в настройках телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Порекомендовать установить GlassWire или проверить «Передачу данных» в настройках телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с тарифом при заморозке?', 'Заморозка останавливает действие тарифа, но сохраняет текущие дни и объём трафика. При разморозке тариф возобновляется с того же места.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф сгорает, деньги возвращаются на баланс', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф сгорает, деньги возвращаются на баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф полностью отключается, оставшиеся дни и трафик аннулируются', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф полностью отключается, оставшиеся дни и трафик аннулируются'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф останавливается, оставшиеся дни и объём трафика сохраняются до разморозки', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф останавливается, оставшиеся дни и объём трафика сохраняются до разморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф продолжает действовать, но скорость снижается', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф продолжает действовать, но скорость снижается'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?', 'Ситуация 1 - «Почему трафик не обновился?». Причины: последний день тарифа, закончились сбросы (сбросов = дней минус 1). Варианта «не подтвердил списание» не существует.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сегодня последний день действия тарифа - суточный сброс не предусмотрен', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сегодня последний день действия тарифа - суточный сброс не предусмотрен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Количество сбросов уже исчерпано (сбросов = количество дней минус 1)', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Количество сбросов уже исчерпано (сбросов = количество дней минус 1)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент забыл подтвердить списание в личном кабинете', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент забыл подтвердить списание в личном кабинете'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?', 'Ситуация 2 - «Во сколько обновляется трафик?». Время сброса каждый абонент выбирает сам при подключении, поэтому у всех оно разное. Оператор смотрит в системе и сообщает.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что у всех абонентов сброс в 00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что у всех абонентов сброс в 00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в системе время сброса для этого абонента и сообщить по МСК (и по местному, если нужно)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в системе время сброса для этого абонента и сообщить по МСК (и по местному, если нужно)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам, чтобы они узнали время сброса', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам, чтобы они узнали время сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответить, что время сброса оператору недоступно', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответить, что время сброса оператору недоступно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?', 'Ситуация 4 - «Трафик быстро закончился после сброса». Система видит общий расход, но не знает, на какие приложения. Рекомендуем установить GlassWire или проверить настройки телефона - раздел «Передача данных».',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам на возврат трафика', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам на возврат трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что трафик мог быть потрачен фоновыми приложениями, и порекомендовать приложение для учёта трафика (GlassWire), а также “Передача данных” в настройках телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что трафик мог быть потрачен фоновыми приложениями, и порекомендовать приложение для учёта трафика (GlassWire), а также “Передача данных” в настройках телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это ошибка системы, и подключить новый пакет вручную', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это ошибка системы, и подключить новый пакет вручную'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перенаправить абонента в службу технической поддержки', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'kuda-uhodit-trafik'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перенаправить абонента в службу технической поддержки'
  );



-- Квиз: Личный кабинет и доступ

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Личный кабинет и доступ', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как восстанавливается пароль?', 'Только через систему. Оператор НЕ диктует пароль — это нарушение безопасности.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как восстанавливается пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор диктует новый пароль', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Как восстанавливается пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор диктует новый пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через систему: нажать «Забыл пароль» → робот звонит → код → новый пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Как восстанавливается пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через систему: нажать «Забыл пароль» → робот звонит → код → новый пароль'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?', 'Сначала сверяем номер. Если верный — рекомендуем сброс через почту. Если не помогло — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить номер в карточке и порекомендовать сброс через почту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить номер в карточке и порекомендовать сброс через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что система сломана', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что система сломана'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?', 'Если нет мобильной связи — восстановление только через электронную почту.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через звонок робота', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никак, нужно ждать приезда специалиста', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никак, нужно ждать приезда специалиста'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?', 'Логин (ID) виден в карточке. Оператор может его сообщить.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую учётную запись', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую учётную запись'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть логин в карточке абонента и сообщить абоненту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть логин в карточке абонента и сообщить абоненту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбросить ЛК через инженеров', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбросить ЛК через инженеров'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?', 'Если почта не привязана — восстановление только по номеру телефона через робота.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через звонок робота', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через чат поддержки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через чат поддержки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит продиктовать пароль. Ваше действие:', 'Диктовать пароль категорически нельзя. Только восстановление через систему.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продиктовать, это быстро', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продиктовать, это быстро'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать: диктовать пароль запрещено политикой безопасности', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать: диктовать пароль запрещено политикой безопасности'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить пароль в письме', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить пароль в письме'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит прислать детализацию трафика на почту. Что делать?', 'Детализация в ЛК. Заявка только если в ЛК не формируется.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что детализация доступна в ЛК (Профиль → История авторизаций). Если не формируется — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что детализация доступна в ЛК (Профиль → История авторизаций). Если не формируется — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что такой функции нет', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что такой функции нет'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?', 'Чаще всего ошибка при регистрации — неверно заполненные поля или слабый пароль.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Настроен ли у него роутер', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Настроен ли у него роутер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Все ли поля заполнены, правильный ли пароль (≥8 символов, загл+строч+цифры)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Все ли поля заполнены, правильный ли пароль (≥8 символов, загл+строч+цифры)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не заблокирован ли он в системе', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не заблокирован ли он в системе'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько времени ждать звонка робота после запроса?', 'Обычно робот звонит в течение минуты. Если прошло больше 5 минут — проверяем номер.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 5 минут', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 5 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 1 минуты', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 1 минуты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?', 'Сначала проверить блокировку звонков и предложить почту. Если не помогло — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 100, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить, не блокирует ли телефон звонки, и предложить восстановление через почту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить, не блокирует ли телефон звонки, и предложить восстановление через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Повторно отправить запрос', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Повторно отправить запрос'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит изменить логин. Что ответить?', 'Логин (ID) — уникальный идентификатор, он не меняется никогда.',
       'single'::helpdesk.kb_question_selection_mode, 110, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Логин можно изменить в ЛК»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Логин можно изменить в ЛК»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Логин — это ваш ID, он не меняется.»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Логин — это ваш ID, он не меняется.»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку на смену логина»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку на смену логина»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?', 'При отсутствии мобильной связи — только восстановление через почту.',
       'single'::helpdesk.kb_question_selection_mode, 120, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через звонок робота', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никак', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никак'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?', 'Для PPPoE логин/пароль «зашиты» в роутер. При смене — заявка инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 130, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что новые настройки нужны в роутере — заявка инженерам', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что новые настройки нужны в роутере — заявка инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать купить другой роутер', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать купить другой роутер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключить через HOTSPOT', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключить через HOTSPOT'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:', 'Абоненты часто не отвечают, потому что не узнают номер. Предупредите заранее.',
       'single'::helpdesk.kb_question_selection_mode, 140, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предупредить заранее: «Вам позвонит робот с неизвестного номера — пожалуйста, ответьте»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предупредить заранее: «Вам позвонит робот с неизвестного номера — пожалуйста, ответьте»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это его проблема', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это его проблема'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?', 'Самый простой способ — сменить пароль от Wi-Fi в ЛК. Все старые подключения сбросятся.',
       'single'::helpdesk.kb_question_selection_mode, 150, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lichnyy-kabinet-i-dostup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );



-- Квиз: Ka/Ku диапазон и линейки тарифов

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Ka/Ku диапазон и линейки тарифов', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком на лимитном тарифе после его исчерпания?', 'На лимитных тарифах при исчерпании трафика доступ приостанавливается. Продление — за 50-100 ₽.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость падает до 128 Кбит/с', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость падает до 128 Кбит/с'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доступ приостанавливается', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доступ приостанавливается'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически подключается Турбо-кнопка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически подключается Турбо-кнопка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?', 'На безлимитных тарифах при превышении дневного лимита скорость падает до 128 Кбит/с. В полночь пакет обновляется.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доступ приостанавливается до полуночи', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доступ приостанавливается до полуночи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость падает до 128 Кбит/с до полуночи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость падает до 128 Кбит/с до полуночи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически списываются деньги', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически списываются деньги'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?', 'Лимитные тарифы — это покупка фиксированного объёма трафика (от 1000 до 100000 МБ). После исчерпания доступ приостанавливается.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Безлимитный', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Безлимитный'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Лимитный', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Лимитный'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Турбо-кнопка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Турбо-кнопка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?', 'Безлимитные тарифы — ежедневное обновление пакета трафика. Подходят для активных пользователей.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Лимитные', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Лимитные'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Безлимитные', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Безлимитные'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Слайдер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Слайдер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Тарифы для юридических лиц обсуждаются:', 'ЮЛ — только через менеджера. Оператор не обсуждает коммерческие условия с юрлицами.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператором напрямую', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператором напрямую'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через менеджера (cm@wifitochka.ru)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через менеджера (cm@wifitochka.ru)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически в ЛК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'lineyki-tarifov'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически в ЛК'
  );



-- Квиз: Медиаконтент / Мультикаст

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Медиаконтент / Мультикаст', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?', 'Оператор не имеет доступа к серверу Мультикаста. Его задача — передать заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить скорость интернета абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить скорость интернета абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Выслушать, успокоить, контейнировать эмоции и создать заявку инженеру', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Выслушать, успокоить, контейнировать эмоции и создать заявку инженеру'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попробовать перезагрузить сервер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попробовать перезагрузить сервер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?', 'Мультикаст — пилотный проект, оператор не имеет доступа к серверу.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что это не входит в его обязанности', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что это не входит в его обязанности'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что Мультикаст — пилотный проект, и его техподдержкой занимаются инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что Мультикаст — пилотный проект, и его техподдержкой занимаются инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что абонент должен сам разобраться', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что абонент должен сам разобраться'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое Мультикаст? Мультикаст?', 'Мультикаст — видеосервис, контент идёт по спутниковому каналу внутри сети.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Новый тарифный план', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Новый тарифный план'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пилотный проект видеосервиса, где абоненты через спутниковый ресурс смотрят видео-контент с сервера', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пилотный проект видеосервиса, где абоненты через спутниковый ресурс смотрят видео-контент с сервера'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Система оплаты через спутник', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Система оплаты через спутник'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?', 'Единственное действие — заявка инженерам с данными. Диагностика на месте не проводится.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить тариф и скорость абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить тариф и скорость абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать перезагрузить устройство', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать перезагрузить устройство'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку с ID, названием контента и устройством', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку с ID, названием контента и устройством'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?', 'Загрузка контента — не на стороне оператора. Фиксируем запрос и передаём инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что контент появится позже', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что контент появится позже'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Записать название, передать заявку инженерам', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Записать название, передать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что контент загружается автоматически', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что контент загружается автоматически'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?', 'Любая попытка «решить на месте» бесполезна, если проблема на сервере Мультикаста.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку инженеру', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку инженеру'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пытаться решить проблему на месте (советовать перезагрузку)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пытаться решить проблему на месте (советовать перезагрузку)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Уточнять название контента и устройство', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Уточнять название контента и устройство'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?', 'Чем больше данных — тем быстрее инженеры разберутся.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента, название контента, устройство, описание ошибки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента, название контента, устройство, описание ошибки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только жалобу без деталей', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только жалобу без деталей'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?', 'Для заявки нужны: название контента, устройство, ошибка.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Почему он хочет посмотреть именно этот фильм', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Почему он хочет посмотреть именно этот фильм'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Название контента, устройство и текст ошибки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Название контента, устройство и текст ошибки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Когда он последний раз перезагружал роутер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'mediakontent-videoservis-multikast'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Когда он последний раз перезагружал роутер'
  );



-- Квиз: Нет подключения к интернету

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Нет подключения к интернету', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'С чего начинается работа с обращением «нет интернета»?', 'Диагностика — первый шаг. Она проверит 6 параметров.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запустить диагностику в карточке абонента', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запустить диагностику в карточке абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить перезагрузить роутер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить перезагрузить роутер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?', 'Если диагностика не показывает проблему — передаём заявку с данными.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить подождать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить подождать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Собрать данные (ID, устройство, тип подключения) и создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Собрать данные (ID, устройство, тип подключения) и создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перезагрузить систему', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перезагрузить систему'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое кнопка «Диагностика» в карточке абонента?', 'Диагностика проверяет: учётная запись, тариф, баланс, станция, сессия, лимит сессий.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Кнопка перезагрузки оборудования', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Кнопка перезагрузки оборудования'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматическая проверка 6 параметров учётной записи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматическая проверка 6 параметров учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создание заявки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создание заявки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Результат диагностики — это:', 'Диагностика — инструмент оператора. Абоненту не нужно знать её результат, ему нужен срок решения.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Результат диагностики — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответ для абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответ для абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инструмент для оператора, чтобы понять причину', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инструмент для оператора, чтобы понять причину'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отчёт для инженеров', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отчёт для инженеров'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Рабочее время инженеров для обработки заявок:', 'Инженеры работают с 8:00 до 16:00 по московскому времени в будние дни.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Круглосуточно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Круглосуточно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8:00–16:00 МСК в будни', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8:00–16:00 МСК в будни'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '9:00–18:00 МСК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '9:00–18:00 МСК'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?', 'Вечером и в выходные — ответ в начале следующего рабочего дня.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через 15 минут', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующего рабочего дня (понедельник)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующего рабочего дня (понедельник)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В субботу днём', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'net-podklyucheniya-k-internetu'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В субботу днём'
  );



-- Квиз: Новые подключения

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Новые подключения', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'novye-podklyucheniya'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужно собрать при обращении потенциального абонента-физлица?', 'Для физлица: ФИО, телефон, адрес, наличие желающих среди соседей (важно для окупаемости установки).',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только телефон', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только телефон'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ФИО, телефон, адрес, есть ли желающие среди соседей', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ФИО, телефон, адрес, есть ли желающие среди соседей'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только адрес', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только адрес'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?', 'Для ЮЛ: ФИО контактного лица, телефон, адрес, потенциальное количество абонентов.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Те же, что для физлица, плюс потенциальное количество абонентов', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Те же, что для физлица, плюс потенциальное количество абонентов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только название организации', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только название организации'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только телефон', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только телефон'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'После сбора данных потенциального абонента оператор должен:', 'Создать заявку на новое подключение с указанием всех данных. Не обещать, что подключение состоится.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать подключение в ближайшее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать подключение в ближайшее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку с указанием всех собранных данных', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку с указанием всех собранных данных'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить на сайт компании', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить на сайт компании'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?', 'Решение принимается на основе количества заявок от жителей. Чем больше желающих — тем выше вероятность.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'От количества желающих подключиться', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'От количества желающих подключиться'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'От суммы, которую готов заплатить абонент', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'От суммы, которую готов заплатить абонент'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ни от чего, мы не подключаем новые НП', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'novye-podklyucheniya'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ни от чего, мы не подключаем новые НП'
  );



-- Квиз: Оплата и проблемы с платежами

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Оплата и проблемы с платежами', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?', 'Платежи обрабатываются до 30 минут.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 24 часов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 24 часов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?', 'Если >30 минут — запрашиваем скриншот справки и передаём инженерам для отслеживания.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить подождать ещё', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить подождать ещё'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот справки об операции из приложения банка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот справки об операции из приложения банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пополнить баланс вручную', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пополнить баланс вручную'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:', 'Автопродление могло подключить тариф — баланс пуст, но тариф активен.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ошибка банка', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ошибка банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сработало автопродление — тариф подключился, деньги на тарифе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сработало автопродление — тариф подключился, деньги на тарифе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги потерялись', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги потерялись'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент отправил платёж, но по ошибке указал неправильную сумму:', 'Излишек можно вернуть на баланс через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не сделать, деньги пропали', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не сделать, деньги пропали'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — инженеры проверят и вернут излишек', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — инженеры проверят и вернут излишек'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить отправить ещё раз', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить отправить ещё раз'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не может оплатить через СБП — ошибка в системе:', 'Если один способ не работает — предложить альтернативу. Если все не работают — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что СБП не работает', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что СБП не работает'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить оплатить другим способом (карта, ЮMoney) или создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить оплатить другим способом (карта, ЮMoney) или создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Игнорировать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Игнорировать'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент оплатил через банк, чек есть, но деньги не пришли:', 'Запросить скриншот справки об операции из приложения банка',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот справки об операции из приложения банка', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот справки об операции из приложения банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать ждать', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать ждать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Срок зачисления платежа на баланс при оплате картой:', 'Платежи обрабатываются до 30 минут.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 2 часов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 2 часов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты', 'Оператор не формирует чеки. Выписку можно получить в банке.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Распечатать и отправить', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Распечатать и отправить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: чек можно получить в своём банке (выписка по операциям)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: чек можно получить в своём банке (выписка по операциям)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на чек', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на чек'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?', 'При отрицательном балансе нужно пополнить счёт для подключения тарифа.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пополнить баланс', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пополнить баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку для разблокировки', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку для разблокировки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подождать автоматического списания', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'oplatil-no-dengi-ne-prishli'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подождать автоматического списания'
  );



-- Квиз: Организационные вопросы

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Организационные вопросы', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'organizatsionnye-voprosy'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?', 'Сменить пароль, автопродление, посмотреть трафик — можно в ЛК. Смена владельца и расторжение — через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить владельца учётной записи', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить владельца учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Расторгнуть договор', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Расторгнуть договор'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Договор оферты можно найти:29. Договор оферты можно найти:', 'Договор оферты в ЛК. Абонент может ознакомиться самостоятельно.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В базе знаний', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В базе знаний'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В ЛК: Профиль → Справочная информация → Договор оферты', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В ЛК: Профиль → Справочная информация → Договор оферты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить у инженеров по заявке', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить у инженеров по заявке'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?', 'Оператор не может расторгнуть договор самостоятельно — только через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Расторгнуть договор самостоятельно в ЛК абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Расторгнуть договор самостоятельно в ЛК абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что расторжение невозможно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что расторжение невозможно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?', 'Смена номера телефона — через заявку. Остальное можно в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Просмотр детализации трафика', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Просмотр детализации трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Смена номера телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Смена номера телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отключение автопродления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'organizatsionnye-voprosy'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отключение автопродления'
  );



-- Квиз: Дополнительные ситуации

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Дополнительные ситуации', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'problemy-s-oborudovaniem'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?', 'Погода (ветер, снег) может влиять на спутниковое оборудование. Если временно — объяснить. Если постоянно — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['problemy-s-oborudovaniem']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'problemy-s-oborudovaniem'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на ремонт', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'problemy-s-oborudovaniem'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на ремонт'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: погода может влиять на спутниковую связь. Если проблема повторится — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'problemy-s-oborudovaniem'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: погода может влиять на спутниковую связь. Если проблема повторится — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'problemy-s-oborudovaniem'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );



-- Квиз: Партнёрская сеть

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Партнёрская сеть', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Каков основной принцип подключения новых населённых пунктов?', 'Новые НП подключаются через местных партнёров-предпринимателей, которые устанавливают оборудование.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через прямой выезд наших инженеров', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через прямой выезд наших инженеров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через развитие партнёрской сети (местных предпринимателей)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через развитие партнёрской сети (местных предпринимателей)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через заявки абонентов на сайте', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через заявки абонентов на сайте'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?', 'Собрать данные и передать заявку. Объяснить, что решение принимается на основе количества желающих.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что подключение невозможно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что подключение невозможно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Собрать данные, создать заявку, объяснить про партнёрскую модель', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Собрать данные, создать заявку, объяснить про партнёрскую модель'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить на сайт', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить на сайт'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'На основной сайт компании мы отправляем:', 'На сайт отправляем только потенциальных партнёров, не физлиц. Под физлиц разработан другой процесс.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'На основной сайт компании мы отправляем:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонентов-физлиц для подключения', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонентов-физлиц для подключения'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только потенциальных партнёров', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только потенциальных партнёров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всех желающих', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всех желающих'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кем может быть партнёр для подключения нового населённого пункта?', 'Партнёр — это местный предприниматель, который устанавливает оборудование и может подключать односельчан.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Любым жителем', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Любым жителем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Местным предпринимателем', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Местным предпринимателем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сотрудником компании', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сотрудником компании'
  );



-- Квиз: Сроки ответа инженеров и РКН-блокировки

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Сроки ответа инженеров и РКН-блокировки', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?', 'Если не работает только конкретный ресурс — скорее всего блокировка РКН.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проблема с его тарифом', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проблема с его тарифом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вероятно, блокировка РКН', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вероятно, блокировка РКН'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проблема с оборудованием', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проблема с оборудованием'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Может ли оператор повлиять на блокировку РКН?', 'РКН-блокировки — не наша ответственность. Только консультация.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, через заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, это требование законодательства, мы не влияем', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, это требование законодательства, мы не влияем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Может, но только для некоторых сайтов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Может, но только для некоторых сайтов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:', 'Если работает всё, кроме одного ресурса — это блокировка/замедление РКН.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку, инженеры проверят»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку, инженеры проверят»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Возможно, это замедление/блокировка РКН. Мы не можем на это повлиять»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Возможно, это замедление/блокировка РКН. Мы не можем на это повлиять»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Проверьте скорость интернета»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Проверьте скорость интернета»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'При РКН-блокировке оператор:', 'Это не техническая проблема. Только консультация абонента.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'При РКН-блокировке оператор:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создаёт заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создаёт заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Даёт консультацию, заявка не создаётся', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Даёт консультацию, заявка не создаётся'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перенаправляет к менеджеру', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'rkn-blokirovki-i-ogranicheniya-dostupa'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перенаправляет к менеджеру'
  );



-- Квиз: Смена тарифа

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Смена тарифа', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'smena-tarifa'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Нужно ли отключать текущий тариф перед подключением нового?', 'Для смены тарифа нужно сначала отключить текущий, потом подключить новый.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, старый тариф нужно отключить', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, старый тариф нужно отключить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, новый подключится автоматически', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, новый подключится автоматически'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не может сменить тариф в ЛК. Ваше действие:', 'Сначала попробовать объяснить. Если не получается — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить пошагово или создать заявку', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить пошагово или создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить тариф через систему', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить тариф через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что смена недоступна', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что смена недоступна'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Можно ли подключить тариф, если на балансе недостаточно средств?', 'Для подключения тарифа должно быть достаточно средств на балансе.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, нужно пополнить баланс', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, нужно пополнить баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, можно в долг', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, можно в долг'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, с последующим списанием', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'smena-tarifa'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, с последующим списанием'
  );



-- Квиз: Сроки ответа инженеров и РКН-блокировки

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Сроки ответа инженеров и РКН-блокировки', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие сроки ответа инженеров на заявку в рабочее время?', 'В рабочее время (8:00–16:00 МСК, будни) ответ — до 15 минут.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 1 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 1 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 15 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 10 минут', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 10 минут'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Заявка подана в воскресенье вечером. Когда ответ?', 'Вечером, в выходные и праздники — ответ в начале следующего рабочего дня.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через 15 минут', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующего рабочего дня (понедельник)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующего рабочего дня (понедельник)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В воскресенье ночью', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В воскресенье ночью'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит точное время ответа инженеров. Что ответить?', 'Всегда называть конкретный срок. «Скоро» — худший вариант.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я не знаю точно, сколько ждать»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я не знаю точно, сколько ждать»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«В рабочее время — до 15 минут. Вечером/в выходные — в начале следующего рабочего дня»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«В рабочее время — до 15 минут. Вечером/в выходные — в начале следующего рабочего дня»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ждите, вам ответят»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sroki-otveta-inzhenerov'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ждите, вам ответят»'
  );



-- Квиз: Суточный сброс / обновление трафика

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Суточный сброс / обновление трафика', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему может не сработать суточный сброс трафика?', 'В последний день тарифа суточный сброс не происходит. Это нормально.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Системная ошибка, нужно перезагрузить', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Системная ошибка, нужно перезагрузить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сегодня последний день действия тарифа — сброс не предусмотрен', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сегодня последний день действия тарифа — сброс не предусмотрен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент не подтвердил списание', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент не подтвердил списание'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?', 'Количество сбросов = количество дней минус 1. Для 30 дней — 29 сбросов.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '30 сбросов', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '30 сбросов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '29 сбросов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '29 сбросов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Количество не ограничено', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Количество не ограничено'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?', 'Время сброса каждый выбирает сам при подключении. Оно разное у всех. Оператор смотрит в системе.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что у всех в 00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что у всех в 00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в системе время сброса для этого абонента и сообщить', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в системе время сброса для этого абонента и сообщить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит изменить время суточного сброса:', 'Время сброса может быть изменено, но только через заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Изменить время самостоятельно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Изменить время самостоятельно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — время сброса меняют инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — время сброса меняют инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что время изменить нельзя', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что время изменить нельзя'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?', 'Причины: последний день тарифа, закончились сбросы, или абонент перепутал дату.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не последний ли день тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не последний ли день тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не ошибся ли абонент днём', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не ошибся ли абонент днём'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всё перечисленное', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всё перечисленное'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для тарифа на 30 дней предоставляется пакетов трафика:', '30 пакетов: первый при подключении + 29 сбросов = 30. Плюс последний день без сброса.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '30 пакетов', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '30 пакетов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '31 пакет (первый при подключении + 29 сбросов + последний день)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '31 пакет (первый при подключении + 29 сбросов + последний день)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:', 'Сначала проверяем причину. Если не последний день и сбросы не закончились — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать ждать до утра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать ждать до утра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить, не последний ли день тарифа. Если нет — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить, не последний ли день тарифа. Если нет — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какое время сброса трафика устанавливается по умолчанию?', 'Время сброса каждый абонент выбирает сам при подключении тарифа.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Время, которое абонент выбрал при подключении', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Время, которое абонент выбрал при подключении'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Суточный сброс — это:', 'Суточный сброс — это обновление дневного лимита трафика.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Суточный сброс — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Списание денег за день', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Списание денег за день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматическое обновление дневного пакета трафика', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматическое обновление дневного пакета трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отключение тарифа на ночь', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отключение тарифа на ночь'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент потратил весь дневной трафик за час. Когда будет сброс?', 'Сброс произойдёт в установленное время (обычно на следующий день).',
       'single'::helpdesk.kb_question_selection_mode, 100, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На следующий день по местному времени сброса', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На следующий день по местному времени сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никогда', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никогда'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько трафика даётся при подключении тарифа сверх сбросов?', 'При подключении тарифа первый пакет трафика даётся сразу + последующие сбросы.',
       'single'::helpdesk.kb_question_selection_mode, 110, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только то, что в пакете', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только то, что в пакете'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Первый пакет даётся сразу при подключении', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Первый пакет даётся сразу при подключении'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не даётся', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не даётся'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?', 'В последний день сброса нет — это учтено в количестве дней (30 дней = 29 сбросов + первый пакет).',
       'single'::helpdesk.kb_question_selection_mode, 120, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это ошибка, я передам заявку»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это ошибка, я передам заявку»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это нормально. В последний день сброс не предусмотрен, трафик первого дня компенсирует это»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это нормально. В последний день сброс не предусмотрен, трафик первого дня компенсирует это»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Подключите новый тариф»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'sutochnyy-sbros-obnovlenie-trafika'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Подключите новый тариф»'
  );



-- Квиз: Возврат денежных средств

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Возврат денежных средств', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о возврате денег?', 'Возвраты и компенсации — только через заявку, решение принимают инженеры.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о возврате денег?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор контакт-центра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор контакт-центра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит вернуть деньги на карту, а не на баланс:', 'Вывод на карту возможен, но по решению инженеров. Только заявка.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Такой возможности нет', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Такой возможности нет'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Можно, но по решению инженеров через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Можно, но по решению инженеров через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть может только оператор', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть может только оператор'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужны для заявки на возврат?', 'В заявке должны быть ID абонента, период и причина возврата.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период и причина возврата', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период и причина возврата'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только сумма', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только сумма'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент заплатил за тариф, но передумал через 5 минут:', 'Если абонент не пользовался — возможен возврат на баланс через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги не возвращаются', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги не возвращаются'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — если трафик не израсходован, возможен возврат на баланс', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — если трафик не израсходован, возможен возврат на баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда абоненту НЕ положен возврат денег?', 'Если абонент сам потратил трафик — возврат не положен.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Была проблема на нашей стороне', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Была проблема на нашей стороне'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент сам израсходовал весь трафик и хочет деньги назад', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент сам израсходовал весь трафик и хочет деньги назад'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Двойное списание по нашей ошибке', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Двойное списание по нашей ошибке'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Возврат на карту осуществляется:', 'Только инженеры принимают решение о выводе средств на карту.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Возврат на карту осуществляется:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'По решению инженеров', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'По решению инженеров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно оператором', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно оператором'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?', 'Компенсируется время фактического простоя, зафиксированное системой.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Весь период тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Весь период тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только время, когда была зафиксирована проблема', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только время, когда была зафиксирована проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не компенсируется', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не компенсируется'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Куда возвращаются средства при компенсации?', 'При компенсации средства возвращаются на баланс ЛК, не на карту.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На карту абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На карту абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На баланс личного кабинета', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На баланс личного кабинета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Наличными', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'trebovanie-vozvrata-deneg'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Наличными'
  );



-- Квиз: Турбо-кнопка

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Турбо-кнопка', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое Турбо-кнопка?', 'Турбо-кнопка восстанавливает дневной лимит на безлимитных тарифах, когда трафик закончился.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое Турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Новый тарифный план', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Новый тарифный план'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Платная опция, которая восстанавливает дневной лимит трафика на безлимитных тарифах', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Платная опция, которая восстанавливает дневной лимит трафика на безлимитных тарифах'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Увеличение скорости интернета', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Увеличение скорости интернета'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопка продлевает срок тарифа?', 'Турбо-кнопка не продлевает тариф. Трафик сгорает вместе с тарифом.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, продлевает на сутки', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, продлевает на сутки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, она только восстанавливает дневной лимит, срок тарифа не меняется', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, она только восстанавливает дневной лимит, срок тарифа не меняется'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продлевает на срок действия кнопки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продлевает на срок действия кнопки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'При каком условии Турбо-кнопка недоступна для подключения?', 'Защита от лишних трат: если осталось >80% пакета — Турбо-кнопка недоступна.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если тариф заканчивается через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если тариф заканчивается через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если у абонента осталось больше 80% дневного пакета трафика', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если у абонента осталось больше 80% дневного пакета трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент уже подключал её сегодня', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент уже подключал её сегодня'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто подключает Турбо-кнопку?', 'Оператор объясняет, как подключить, но не делает это сам. Подключение в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженер по заявке', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженер по заявке'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент самостоятельно в личном кабинете', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент самостоятельно в личном кабинете'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:', 'Если трафик не был потрачен — возврат возможен, но только через заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги нельзя', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги нельзя'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — возврат возможен, если трафик не был израсходован', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — возврат возможен, если трафик не был израсходован'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопку можно подключить:', 'Турбо-кнопка подключается в ЛК. Оператор только объясняет, как это сделать.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопку можно подключить:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только по звонку оператору', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только по звонку оператору'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В личном кабинете абонента', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В личном кабинете абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через SMS', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через SMS'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?', 'Турбо-кнопка не продлевает тариф. Если срок тарифа истёк — весь неизрасходованный трафик сгорает.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик переносится на следующий тариф', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик переносится на следующий тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сгорает вместе с тарифом', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сгорает вместе с тарифом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик замораживается до продления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик замораживается до продления'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для каких тарифов предназначена Турбо-кнопка?', 'Турбо-кнопка работает на безлимитных тарифах, восстанавливая дневной лимит.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для всех тарифов без исключения', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для всех тарифов без исключения'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для безлимитных тарифов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для безлимитных тарифов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только для лимитных тарифов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'turbo-knopka'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только для лимитных тарифов'
  );



-- Квиз: Дополнительные ситуации

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Дополнительные ситуации', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?', 'Ситуация 1 + Главное правило',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['voprosy-po-spisaniyam-i-rashodam']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, оператор может самостоятельно восстановить остаток через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, оператор может самостоятельно восстановить остаток через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, оператор не восстанавливает трафик самостоятельно. Нужно объяснить абоненту, что информация передана специалистам, и создать заявку инженерам', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, оператор не восстанавливает трафик самостоятельно. Нужно объяснить абоненту, что информация передана специалистам, и создать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, остаток сгорает, и абоненту нужно купить новый тариф', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, остаток сгорает, и абоненту нужно купить новый тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Списание с карты не отображается в системе. Что передать инженерам?', 'Нужен полный комплект: ID, дата, время, сумма, чек, комментарий.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['voprosy-po-spisaniyam-i-rashodam']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, дату/время, сумму, скриншот чека с комментарием', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, дату/время, сумму, скриншот чека с комментарием'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только скриншот', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'voprosy-po-spisaniyam-i-rashodam'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только скриншот'
  );



-- Квиз: Восстановление трафика

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Восстановление трафика', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:', 'Оператор не принимает решений о компенсации. Только заявка.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это не наша проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это не наша проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на компенсацию, решение за инженерами', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на компенсацию, решение за инженерами'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Создавая заявку на восстановление трафика, обязательно указать:', 'В заявке должны быть ID, период простоя и причина.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период простоя и причину', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период простоя и причину'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID и сумму компенсации', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID и сумму компенсации'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о компенсации трафика?', 'Только инженер. Оператор создаёт заявку.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженер', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Можно ли восстановить трафик, если у абонента был отключён свет?', 'Внешние причины (свет, погода) — компенсация по решению инженеров через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, это не наша ответственность', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, это не наша ответственность'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, но по решению инженеров через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, но по решению инженеров через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, автоматически', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, автоматически'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В заявке на компенсацию трафика нужно указать:', 'ID, период и причина — обязательные поля для заявки.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Прошу компенсировать» без деталей', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Прошу компенсировать» без деталей'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период простоя, причина (что произошло)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период простоя, причина (что произошло)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона абонента', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона абонента'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?', 'Если не уверены — создавайте заявку. Решение примут инженеры. Не обещайте того, в чём не уверены.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать, так как не уверены', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать, так как не уверены'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — пусть инженеры решают', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — пусть инженеры решают'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать компенсацию, чтобы успокоить', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'vosstanovlenie-trafika'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать компенсацию, чтобы успокоить'
  );



-- Квиз: Заморозка / разморозка тарифа

INSERT INTO helpdesk.kb_quizzes (article_id, title, description, is_active, passing_score_percent)
SELECT a.id, 'Проверка знаний: Заморозка / разморозка тарифа', '', TRUE, 100
FROM helpdesk.kb_articles a
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (SELECT 1 FROM helpdesk.kb_quizzes q WHERE q.article_id = a.id);

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое заморозка тарифа?', 'Заморозка — это временная приостановка тарифа. Трафик и срок сохраняются.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое заморозка тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Полное отключение интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Полное отключение интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Приостановка действия тарифа с сохранением остатка трафика и срока', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Приостановка действия тарифа с сохранением остатка трафика и срока'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Удаление учётной записи', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Удаление учётной записи'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда нужна заморозка тарифа?', 'Заморозка для случаев, когда абонент временно не пользуется интернетом (поездка, ремонт).',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда нужна заморозка тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент хочет сменить тариф', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент хочет сменить тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент уезжает и временно не будет пользоваться интернетом', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент уезжает и временно не будет пользоваться интернетом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент недоволен скоростью', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент недоволен скоростью'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком при заморозке?', 'При заморозке весь неизрасходованный трафик сохраняется.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сгорает', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сгорает'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сохраняется и становится доступен после разморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сохраняется и становится доступен после разморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик переносится на другой тариф', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик переносится на другой тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит со сроком тарифа при заморозке?', 'Срок тарифа приостанавливается на время заморозки.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок продолжает идти', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок продолжает идти'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок приостанавливается на время заморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок приостанавливается на время заморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок сокращается вдвое', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок сокращается вдвое'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?', 'Объяснить причину, заморозить тариф',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это не наша проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это не наша проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: оборудование не работает без электричества. Заморозить тариф', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: оборудование не работает без электричества. Заморозить тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать компенсацию', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать компенсацию'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?', 'Ситуация 1 - «Заморозьте тариф». Оператор сначала предлагает сделать это самостоятельно в ЛК. Если не получается - заявка инженерам. Диктовать телефон инженера абоненту запрещено.',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам на заморозку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам на заморозку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить абоненту заморозить тариф самостоятельно в личном кабинете (вкладка «Тарифы»)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить абоненту заморозить тариф самостоятельно в личном кабинете (вкладка «Тарифы»)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что заморозка больше недоступна', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что заморозка больше недоступна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Передать номер телефона инженера абоненту', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Передать номер телефона инженера абоненту'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько раз за один тариф можно воспользоваться функцией заморозки?', 'Функция заморозки даётся один раз за весь тариф. Заморозка + разморозка = одно использование. Это ключевое ограничение.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Неограниченное количество раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Неограниченное количество раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '2 раза', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '2 раза'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '1 раз', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '1 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '3 раза', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '3 раза'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?', 'Ситуация 4 - «Заморозка при проблемах с сетью». Если проблема на стороне провайдера, инженеры сами решают. Создаётся заявка.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать, так как заморозка даётся только 1 раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать, так как заморозка даётся только 1 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить заморозить через ЛК и скинуть инструкцию', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить заморозить через ЛК и скинуть инструкцию'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам с указанием причины «проблемы с сетью», так как в таких случаях инженеры сами решают вопрос с заморозкой', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам с указанием причины «проблемы с сетью», так как в таких случаях инженеры сами решают вопрос с заморозкой'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать абоненту купить новый тариф', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать абоненту купить новый тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?', 'Если абонент просит заморозить с определённой даты, нужно передать конкретную дату в заявку вместе с ID абонента.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента и желаемую дату заморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента и желаемую дату заморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только желаемую дату', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только желаемую дату'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего, заморозка действует с момента подачи заявки', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'zamorozka-razmorozka-tarifa'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего, заморозка действует с момента подачи заявки'
  );



-- -----------------------------------------------------------------------------

-- Полный пул в daily-warmup (все 171 вопроса для ежедневного теста)

-- -----------------------------------------------------------------------------

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?', 'Первое правило работы с жалобой — не принимать на свой счёт и не защищаться. Признать эмоции абонента и перевести в конструктив.',
       'single'::helpdesk.kb_question_selection_mode, 10, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что вы не виноваты, и перечислить причины', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что вы не виноваты, и перечислить причины'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не защищаться и признать: «Понимаю ваше недовольство, давайте разберёмся»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не защищаться и признать: «Понимаю ваше недовольство, давайте разберёмся»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что надо подождать и переключить на инженера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «У вас вечно всё не работает, вы никто не помогаете». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что надо подождать и переключить на инженера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент требует: «Соедините с руководителем!». Как реагировать?', 'Отказывать в соединении с руководителем нельзя. Но номер телефона не даём — только передаём запрос.',
       'single'::helpdesk.kb_question_selection_mode, 20, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что руководитель занят, и попросить подождать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что руководитель занят, и попросить подождать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не отказывать. Спокойно ответить: «Я передам ваш запрос, с вами свяжутся»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не отказывать. Спокойно ответить: «Я передам ваш запрос, с вами свяжутся»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Дать номер телефона руководителя', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент требует: «Соедините с руководителем!». Как реагировать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Дать номер телефона руководителя'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза лучше всего снижает напряжение?', 'Фраза «я понимаю» снимает половину напряжения. Шаблонные фразы («ваше мнение важно для нас») звучат как насмешка.',
       'single'::helpdesk.kb_question_selection_mode, 30, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ваше мнение важно для нас»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ваше мнение важно для нас»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы не правы, давайте посмотрим факты»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы не правы, давайте посмотрим факты»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я понимаю, это неприятно. Давайте посмотрим, что можно сделать»', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза лучше всего снижает напряжение?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я понимаю, это неприятно. Давайте посмотрим, что можно сделать»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?', 'Нужно найти историю, извиниться за ожидание и дать конкретный срок решения.',
       'single'::helpdesk.kb_question_selection_mode, 40, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить историю обращений и извиниться за ожидание', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить историю обращений и извиниться за ожидание'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что надо подождать, заявка уже есть', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что надо подождать, заявка уже есть'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую заявку с нуля', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я уже 5 раз писал, никто не отвечает». Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую заявку с нуля'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Чего НЕЛЬЗЯ делать при работе с жалобой?', 'Перебивать и спорить нельзя. Признавать проблему и давать срок — можно и нужно.',
       'single'::helpdesk.kb_question_selection_mode, 50, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Признавать проблему и извиняться', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Признавать проблему и извиняться'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перебивать абонента и спорить с ним', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перебивать абонента и спорить с ним'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Давать конкретный срок решения', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чего НЕЛЬЗЯ делать при работе с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Давать конкретный срок решения'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза НЕ годится для работы с жалобой?', 'Фраза «это не в моих обязанностях» вызывает раздражение. Лучше: «Я передам ваш вопрос специалисту»',
       'single'::helpdesk.kb_question_selection_mode, 60, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я понимаю ваше недовольство»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я понимаю ваше недовольство»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это не входит в мои обязанности»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это не входит в мои обязанности»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Давайте посмотрим, что показывает система»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза НЕ годится для работы с жалобой?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?', 'На недоверие нельзя обижаться. Объяснять просто и по делу, без шаблонных фраз.',
       'single'::helpdesk.kb_question_selection_mode, 70, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доказать, что он не прав, привести факты', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доказать, что он не прав, привести факты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не обижаться. Объяснять просто без шаблонов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не обижаться. Объяснять просто без шаблонов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Передать заявку инженерам', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Вы меня обманываете, это развод». Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Передать заявку инженерам'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Главное правило работы с жалобой — это:', 'Жалоба — это сигнал о проблеме. Абонент злится на ситуацию, не на вас лично.',
       'single'::helpdesk.kb_question_selection_mode, 80, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Главное правило работы с жалобой — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Как можно быстрее завершить диалог', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Как можно быстрее завершить диалог'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Жалоба — это не нападение, а сигнал', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Жалоба — это не нападение, а сигнал'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всегда предлагать компенсацию', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Главное правило работы с жалобой — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всегда предлагать компенсацию'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Вместо «Ожидайте» лучше сказать:', 'Конкретный срок снимает тревожность. «Скоро» — худший вариант, абонент не знает, сколько ждать.',
       'single'::helpdesk.kb_question_selection_mode, 90, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Скоро всё сделаем»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Скоро всё сделаем»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ориентировочно до [срок], я прослежу, и вернусь к вам с обратной связью»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ориентировочно до [срок], я прослежу, и вернусь к вам с обратной связью»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вам перезвонят»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Вместо «Ожидайте» лучше сказать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вам перезвонят»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делать в первые 30 секунд разговора с разгневанным абонентом?', 'Первые 30 секунд абонент сбрасывает эмоции. В это время бесполезно что-то объяснять.',
       'single'::helpdesk.kb_question_selection_mode, 100, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Начинать диагностику', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Начинать диагностику'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Дать выговориться, не перебивать', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Дать выговориться, не перебивать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу извиниться за всё', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать в первые 30 секунд разговора с разгневанным абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу извиниться за всё'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какая фраза-помощник правильная?', 'Фраза «вы не правы» удваивает напряжение. Нужно без обвинения переводить в конструктив.',
       'single'::helpdesk.kb_question_selection_mode, 110, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какая фраза-помощник правильная?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы не правы, давайте посмотрим, что показывает система»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы не правы, давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Давайте посмотрим, что показывает система»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Давайте посмотрим, что показывает система»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Вы ошибаетесь, проверьте ещё раз»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какая фраза-помощник правильная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Вы ошибаетесь, проверьте ещё раз»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Лучший способ перевести абонента из эмоций в конструктив:', 'Конкретное действие переключает внимание абонента с эмоций на решение.',
       'single'::helpdesk.kb_question_selection_mode, 120, TRUE,
       ARRAY['kak-otrabatyvat-zhaloby']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать «успокойтесь»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать «успокойтесь»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить конкретное действие: «Давайте я проверю по вашей учётной записи»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить конкретное действие: «Давайте я проверю по вашей учётной записи»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать всё вернуть', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Лучший способ перевести абонента из эмоций в конструктив:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать всё вернуть'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?', 'Оператор не имеет доступа к серверу Мультикаста. Его задача — передать заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 130, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить скорость интернета абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить скорость интернета абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Выслушать, успокоить, контейнировать эмоции и создать заявку инженеру', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Выслушать, успокоить, контейнировать эмоции и создать заявку инженеру'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попробовать перезагрузить сервер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какова единственная задача оператора при обращении по теме «Мультикаст»?Мультикаст»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попробовать перезагрузить сервер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?', 'Мультикаст — пилотный проект, оператор не имеет доступа к серверу.',
       'single'::helpdesk.kb_question_selection_mode, 140, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что это не входит в его обязанности', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что это не входит в его обязанности'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что Мультикаст — пилотный проект, и его техподдержкой занимаются инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что Мультикаст — пилотный проект, и его техподдержкой занимаются инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что абонент должен сам разобраться', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему оператор не должен пытаться диагностировать проблему Мультикаста?Мультикаста?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что абонент должен сам разобраться'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое Мультикаст? Мультикаст?', 'Мультикаст — видеосервис, контент идёт по спутниковому каналу внутри сети.',
       'single'::helpdesk.kb_question_selection_mode, 150, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Новый тарифный план', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Новый тарифный план'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пилотный проект видеосервиса, где абоненты через спутниковый ресурс смотрят видео-контент с сервера', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пилотный проект видеосервиса, где абоненты через спутниковый ресурс смотрят видео-контент с сервера'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Система оплаты через спутник', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Мультикаст? Мультикаст?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Система оплаты через спутник'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?', 'Единственное действие — заявка инженерам с данными. Диагностика на месте не проводится.',
       'single'::helpdesk.kb_question_selection_mode, 160, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить тариф и скорость абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить тариф и скорость абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать перезагрузить устройство', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать перезагрузить устройство'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку с ID, названием контента и устройством', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент сообщает, что видео на Мультикасте не грузится. Ваше действие?Мультикасте не грузится. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку с ID, названием контента и устройством'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?', 'Загрузка контента — не на стороне оператора. Фиксируем запрос и передаём инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 170, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что контент появится позже', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что контент появится позже'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Записать название, передать заявку инженерам', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Записать название, передать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что контент загружается автоматически', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит добавить конкретный контент (фильм, серию). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что контент загружается автоматически'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?', 'Любая попытка «решить на месте» бесполезна, если проблема на сервере Мультикаста.',
       'single'::helpdesk.kb_question_selection_mode, 180, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку инженеру', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку инженеру'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пытаться решить проблему на месте (советовать перезагрузку)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пытаться решить проблему на месте (советовать перезагрузку)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Уточнять название контента и устройство', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что НЕ должен делать оператор при обращении по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Уточнять название контента и устройство'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?', 'Чем больше данных — тем быстрее инженеры разберутся.',
       'single'::helpdesk.kb_question_selection_mode, 190, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента, название контента, устройство, описание ошибки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента, название контента, устройство, описание ошибки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только жалобу без деталей', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какую информацию обязательно передать в заявке по Мультикасту?Мультикасту?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только жалобу без деталей'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?', 'Для заявки нужны: название контента, устройство, ошибка.',
       'single'::helpdesk.kb_question_selection_mode, 200, TRUE,
       ARRAY['mediakontent-videoservis-multikast']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Почему он хочет посмотреть именно этот фильм', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Почему он хочет посмотреть именно этот фильм'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Название контента, устройство и текст ошибки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Название контента, устройство и текст ошибки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Когда он последний раз перезагружал роутер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?0. Абонент говорит: «Фильм не открывается, пишет ошибку». Что уточнить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Когда он последний раз перезагружал роутер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?', 'ЮЛ и партнёры — к менеджеру. Контакты: cm@wifitochka.ru, 8:00–16:00 МСК.',
       'single'::helpdesk.kb_question_selection_mode, 210, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, где в ЛК посмотреть', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, где в ЛК посмотреть'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Направить к менеджеру по работе с клиентами и партнёрами', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?1. Если обращается юридическое лицо по финансовому вопросу и документам, что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Направить к менеджеру по работе с клиентами и партнёрами'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?', 'Оператор не принимает финансовых решений. Возвраты делают только инженеры через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 220, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор контакт-центра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор контакт-центра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денежных средств?2. Кто принимает решение о возврате денежных средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:', 'Менеджер работает с 8:00 до 16:00 по Москве в будни.',
       'single'::helpdesk.kb_question_selection_mode, 230, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '9:00–18:00 МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '9:00–18:00 МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8:00–16:00 МСК', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8:00–16:00 МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Круглосуточно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочие часы менеджера для ЮЛ и партнёров:3. Рабочие часы менеджера для ЮЛ и партнёров:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Круглосуточно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:', 'Оператор фиксирует запрос и передаёт. Документы готовят инженеры или менеджер.',
       'single'::helpdesk.kb_question_selection_mode, 240, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Распечатать и отправить документы', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Распечатать и отправить документы'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Корректно зафиксировать обращение и передать', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Корректно зафиксировать обращение и передать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что документы не предоставляются', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если у абонента запрос на получение документов (счета, договора) — задача оператора:4. Если у абонента запрос на получение документов (счета, договора) — задача оператора:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что документы не предоставляются'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?', 'Оператор не возвращает деньги. Только заявка, решение принимает инженер.',
       'single'::helpdesk.kb_question_selection_mode, 250, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что возврат невозможен', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что возврат невозможен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на компенсацию с ID, периодом и причиной', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на компенсацию с ID, периодом и причиной'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно через систему', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?5. Абонент просит вернуть деньги, потому что не пользовался интернетом из-за отключения. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно через систему'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:', 'Проверяем историю (видно подключение и отключение). Если случайно — заявка на возврат.',
       'single'::helpdesk.kb_question_selection_mode, 260, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что это его проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что это его проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить историю операций и создать заявку на возврат', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить историю операций и создать заявку на возврат'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключить тариф обратно самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:6. Абонент случайно отключил тариф и просит вернуть деньги. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключить тариф обратно самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):', 'Вывод на карту — по решению инженеров через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 270, TRUE,
       ARRAY['finansovye-voprosy-i-dokumenty']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это делает оператор через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это делает оператор через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: вывод на карту возможен по решению инженеров, создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: вывод на карту возможен по решению инженеров, создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что вывод только на баланс', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если абонент хочет вывести остаток средств на карту (не на баланс):27. Если абонент хочет вывести остаток средств на карту (не на баланс):'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что вывод только на баланс'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?', 'Сменить пароль, автопродление, посмотреть трафик — можно в ЛК. Смена владельца и расторжение — через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 280, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить владельца учётной записи', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить владельца учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Расторгнуть договор', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного абонент может сделать самостоятельно в ЛК?28. Что из перечисленного абонент может сделать самостоятельно в ЛК?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Расторгнуть договор'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Договор оферты можно найти:29. Договор оферты можно найти:', 'Договор оферты в ЛК. Абонент может ознакомиться самостоятельно.',
       'single'::helpdesk.kb_question_selection_mode, 290, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В базе знаний', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В базе знаний'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В ЛК: Профиль → Справочная информация → Договор оферты', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В ЛК: Профиль → Справочная информация → Договор оферты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить у инженеров по заявке', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Договор оферты можно найти:29. Договор оферты можно найти:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить у инженеров по заявке'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?', 'Оператор не может расторгнуть договор самостоятельно — только через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 300, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Расторгнуть договор самостоятельно в ЛК абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Расторгнуть договор самостоятельно в ЛК абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что расторжение невозможно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как поступить, если абонент хочет расторгнуть договор?30. Как поступить, если абонент хочет расторгнуть договор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что расторжение невозможно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?', 'Смена номера телефона — через заявку. Остальное можно в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 310, TRUE,
       ARRAY['organizatsionnye-voprosy']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Просмотр детализации трафика', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Просмотр детализации трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Смена номера телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Смена номера телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отключение автопродления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что из перечисленного требует обязательной заявки?1. Что из перечисленного требует обязательной заявки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отключение автопродления'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как восстанавливается пароль?', 'Только через систему. Оператор НЕ диктует пароль — это нарушение безопасности.',
       'single'::helpdesk.kb_question_selection_mode, 320, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как восстанавливается пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор диктует новый пароль', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как восстанавливается пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор диктует новый пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через систему: нажать «Забыл пароль» → робот звонит → код → новый пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как восстанавливается пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через систему: нажать «Забыл пароль» → робот звонит → код → новый пароль'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?', 'Сначала сверяем номер. Если верный — рекомендуем сброс через почту. Если не помогло — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 330, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить номер в карточке и порекомендовать сброс через почту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить номер в карточке и порекомендовать сброс через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что система сломана', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Робот не звонит после запроса восстановления. Что делать в первую очередь?34. Робот не звонит после запроса восстановления. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что система сломана'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?', 'Если нет мобильной связи — восстановление только через электронную почту.',
       'single'::helpdesk.kb_question_selection_mode, 340, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через звонок робота', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никак, нужно ждать приезда специалиста', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?35. В населённом пункте нет мобильной связи. Как абонент может восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никак, нужно ждать приезда специалиста'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?', 'Логин (ID) виден в карточке. Оператор может его сообщить.',
       'single'::helpdesk.kb_question_selection_mode, 350, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую учётную запись', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую учётную запись'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть логин в карточке абонента и сообщить абоненту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть логин в карточке абонента и сообщить абоненту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбросить ЛК через инженеров', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не помнит логин. Что делать?36. Абонент не помнит логин. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбросить ЛК через инженеров'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?', 'Если почта не привязана — восстановление только по номеру телефона через робота.',
       'single'::helpdesk.kb_question_selection_mode, 360, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через звонок робота', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через чат поддержки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой способ восстановления пароля работает, если почта не привязана?37. Какой способ восстановления пароля работает, если почта не привязана?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через чат поддержки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит продиктовать пароль. Ваше действие:', 'Диктовать пароль категорически нельзя. Только восстановление через систему.',
       'single'::helpdesk.kb_question_selection_mode, 370, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продиктовать, это быстро', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продиктовать, это быстро'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать: диктовать пароль запрещено политикой безопасности', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать: диктовать пароль запрещено политикой безопасности'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить пароль в письме', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит продиктовать пароль. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить пароль в письме'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит прислать детализацию трафика на почту. Что делать?', 'Детализация в ЛК. Заявка только если в ЛК не формируется.',
       'single'::helpdesk.kb_question_selection_mode, 380, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что детализация доступна в ЛК (Профиль → История авторизаций). Если не формируется — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что детализация доступна в ЛК (Профиль → История авторизаций). Если не формируется — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что такой функции нет', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит прислать детализацию трафика на почту. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что такой функции нет'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?', 'Чаще всего ошибка при регистрации — неверно заполненные поля или слабый пароль.',
       'single'::helpdesk.kb_question_selection_mode, 390, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Настроен ли у него роутер', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Настроен ли у него роутер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Все ли поля заполнены, правильный ли пароль (≥8 символов, загл+строч+цифры)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Все ли поля заполнены, правильный ли пароль (≥8 символов, загл+строч+цифры)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не заблокирован ли он в системе', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент регистрируется, но выдаёт ошибку. Что проверить в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не заблокирован ли он в системе'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько времени ждать звонка робота после запроса?', 'Обычно робот звонит в течение минуты. Если прошло больше 5 минут — проверяем номер.',
       'single'::helpdesk.kb_question_selection_mode, 400, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 5 минут', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 5 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 1 минуты', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 1 минуты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени ждать звонка робота после запроса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?', 'Сначала проверить блокировку звонков и предложить почту. Если не помогло — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 410, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создавать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создавать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить, не блокирует ли телефон звонки, и предложить восстановление через почту', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить, не блокирует ли телефон звонки, и предложить восстановление через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Повторно отправить запрос', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент уже 10 минут ждёт звонок робота — не звонит. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Повторно отправить запрос'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит изменить логин. Что ответить?', 'Логин (ID) — уникальный идентификатор, он не меняется никогда.',
       'single'::helpdesk.kb_question_selection_mode, 420, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Логин можно изменить в ЛК»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Логин можно изменить в ЛК»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Логин — это ваш ID, он не меняется.»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Логин — это ваш ID, он не меняется.»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку на смену логина»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить логин. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку на смену логина»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:', 'Оператор не принимает решений о компенсации. Только заявка.',
       'single'::helpdesk.kb_question_selection_mode, 430, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это не наша проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это не наша проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на компенсацию, решение за инженерами', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на компенсацию, решение за инженерами'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил Турбо-кнопку, но из-за погоды не смог пользоваться. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Создавая заявку на восстановление трафика, обязательно указать:', 'В заявке должны быть ID, период простоя и причина.',
       'single'::helpdesk.kb_question_selection_mode, 440, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период простоя и причину', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период простоя и причину'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID и сумму компенсации', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Создавая заявку на восстановление трафика, обязательно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID и сумму компенсации'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о компенсации трафика?', 'Только инженер. Оператор создаёт заявку.',
       'single'::helpdesk.kb_question_selection_mode, 450, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженер', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о компенсации трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Можно ли восстановить трафик, если у абонента был отключён свет?', 'Внешние причины (свет, погода) — компенсация по решению инженеров через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 460, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, это не наша ответственность', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, это не наша ответственность'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, но по решению инженеров через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, но по решению инженеров через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, автоматически', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли восстановить трафик, если у абонента был отключён свет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, автоматически'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В заявке на компенсацию трафика нужно указать:', 'ID, период и причина — обязательные поля для заявки.',
       'single'::helpdesk.kb_question_selection_mode, 470, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Прошу компенсировать» без деталей', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Прошу компенсировать» без деталей'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период простоя, причина (что произошло)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период простоя, причина (что произошло)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона абонента', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В заявке на компенсацию трафика нужно указать:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона абонента'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?', 'Если не уверены — создавайте заявку. Решение примут инженеры. Не обещайте того, в чём не уверены.',
       'single'::helpdesk.kb_question_selection_mode, 480, TRUE,
       ARRAY['vosstanovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать, так как не уверены', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать, так как не уверены'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — пусть инженеры решают', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — пусть инженеры решают'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать компенсацию, чтобы успокоить', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делать, если абонент настаивает на компенсации, а вы не уверены в причине?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать компенсацию, чтобы успокоить'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое Турбо-кнопка?', 'Турбо-кнопка восстанавливает дневной лимит на безлимитных тарифах, когда трафик закончился.',
       'single'::helpdesk.kb_question_selection_mode, 490, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое Турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Новый тарифный план', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Новый тарифный план'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Платная опция, которая восстанавливает дневной лимит трафика на безлимитных тарифах', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Платная опция, которая восстанавливает дневной лимит трафика на безлимитных тарифах'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Увеличение скорости интернета', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Увеличение скорости интернета'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопка продлевает срок тарифа?', 'Турбо-кнопка не продлевает тариф. Трафик сгорает вместе с тарифом.',
       'single'::helpdesk.kb_question_selection_mode, 500, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, продлевает на сутки', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, продлевает на сутки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, она только восстанавливает дневной лимит, срок тарифа не меняется', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, она только восстанавливает дневной лимит, срок тарифа не меняется'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продлевает на срок действия кнопки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает срок тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продлевает на срок действия кнопки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'При каком условии Турбо-кнопка недоступна для подключения?', 'Защита от лишних трат: если осталось >80% пакета — Турбо-кнопка недоступна.',
       'single'::helpdesk.kb_question_selection_mode, 510, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если тариф заканчивается через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если тариф заканчивается через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если у абонента осталось больше 80% дневного пакета трафика', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если у абонента осталось больше 80% дневного пакета трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент уже подключал её сегодня', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При каком условии Турбо-кнопка недоступна для подключения?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент уже подключал её сегодня'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто подключает Турбо-кнопку?', 'Оператор объясняет, как подключить, но не делает это сам. Подключение в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 520, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инженер по заявке', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инженер по заявке'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент самостоятельно в личном кабинете', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто подключает Турбо-кнопку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент самостоятельно в личном кабинете'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:', 'Если трафик не был потрачен — возврат возможен, но только через заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 530, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги нельзя', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги нельзя'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — возврат возможен, если трафик не был израсходован', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — возврат возможен, если трафик не был израсходован'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги самостоятельно', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент случайно подключил Турбо-кнопку и хочет вернуть деньги:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги самостоятельно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопку можно подключить:', 'Турбо-кнопка подключается в ЛК. Оператор только объясняет, как это сделать.',
       'single'::helpdesk.kb_question_selection_mode, 540, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопку можно подключить:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только по звонку оператору', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только по звонку оператору'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В личном кабинете абонента', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В личном кабинете абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через SMS', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопку можно подключить:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через SMS'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?', 'Турбо-кнопка не продлевает тариф. Если срок тарифа истёк — весь неизрасходованный трафик сгорает.',
       'single'::helpdesk.kb_question_selection_mode, 550, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик переносится на следующий тариф', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик переносится на следующий тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сгорает вместе с тарифом', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сгорает вместе с тарифом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик замораживается до продления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком Турбо-кнопки, если срок тарифа истекает?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик замораживается до продления'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для каких тарифов предназначена Турбо-кнопка?', 'Турбо-кнопка работает на безлимитных тарифах, восстанавливая дневной лимит.',
       'single'::helpdesk.kb_question_selection_mode, 560, TRUE,
       ARRAY['turbo-knopka']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для всех тарифов без исключения', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для всех тарифов без исключения'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для безлимитных тарифов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для безлимитных тарифов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только для лимитных тарифов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для каких тарифов предназначена Турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только для лимитных тарифов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему может не сработать суточный сброс трафика?', 'В последний день тарифа суточный сброс не происходит. Это нормально.',
       'single'::helpdesk.kb_question_selection_mode, 570, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Системная ошибка, нужно перезагрузить', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Системная ошибка, нужно перезагрузить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сегодня последний день действия тарифа — сброс не предусмотрен', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сегодня последний день действия тарифа — сброс не предусмотрен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент не подтвердил списание', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему может не сработать суточный сброс трафика?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент не подтвердил списание'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?', 'Количество сбросов = количество дней минус 1. Для 30 дней — 29 сбросов.',
       'single'::helpdesk.kb_question_selection_mode, 580, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '30 сбросов', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '30 сбросов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '29 сбросов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '29 сбросов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Количество не ограничено', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько сбросов трафика предусмотрено для тарифа на 30 дней?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Количество не ограничено'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?', 'Время сброса каждый выбирает сам при подключении. Оно разное у всех. Оператор смотрит в системе.',
       'single'::helpdesk.kb_question_selection_mode, 590, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что у всех в 00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что у всех в 00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в системе время сброса для этого абонента и сообщить', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в системе время сброса для этого абонента и сообщить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает, во сколько у него обновляется трафик. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит изменить время суточного сброса:', 'Время сброса может быть изменено, но только через заявку инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 600, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Изменить время самостоятельно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Изменить время самостоятельно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — время сброса меняют инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — время сброса меняют инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что время изменить нельзя', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит изменить время суточного сброса:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что время изменить нельзя'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?', 'Причины: последний день тарифа, закончились сбросы, или абонент перепутал дату.',
       'single'::helpdesk.kb_question_selection_mode, 610, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не последний ли день тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не последний ли день тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не ошибся ли абонент днём', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не ошибся ли абонент днём'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всё перечисленное', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 14:00: «У меня не обновился трафик, хотя сегодня должно было быть обновление». Что проверить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всё перечисленное'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для тарифа на 30 дней предоставляется пакетов трафика:', '30 пакетов: первый при подключении + 29 сбросов = 30. Плюс последний день без сброса.',
       'single'::helpdesk.kb_question_selection_mode, 620, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '30 пакетов', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '30 пакетов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '31 пакет (первый при подключении + 29 сбросов + последний день)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '31 пакет (первый при подключении + 29 сбросов + последний день)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для тарифа на 30 дней предоставляется пакетов трафика:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:', 'Сначала проверяем причину. Если не последний день и сбросы не закончились — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 630, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать ждать до утра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать ждать до утра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить, не последний ли день тарифа. Если нет — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить, не последний ли день тарифа. Если нет — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в 23:00: «Трафик не обновился». Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какое время сброса трафика устанавливается по умолчанию?', 'Время сброса каждый абонент выбирает сам при подключении тарифа.',
       'single'::helpdesk.kb_question_selection_mode, 640, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Время, которое абонент выбрал при подключении', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Время, которое абонент выбрал при подключении'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какое время сброса трафика устанавливается по умолчанию?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Суточный сброс — это:', 'Суточный сброс — это обновление дневного лимита трафика.',
       'single'::helpdesk.kb_question_selection_mode, 650, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Суточный сброс — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Списание денег за день', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Списание денег за день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматическое обновление дневного пакета трафика', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматическое обновление дневного пакета трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отключение тарифа на ночь', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Суточный сброс — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отключение тарифа на ночь'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент потратил весь дневной трафик за час. Когда будет сброс?', 'Сброс произойдёт в установленное время (обычно на следующий день).',
       'single'::helpdesk.kb_question_selection_mode, 660, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На следующий день по местному времени сброса', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На следующий день по местному времени сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никогда', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент потратил весь дневной трафик за час. Когда будет сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никогда'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько трафика даётся при подключении тарифа сверх сбросов?', 'При подключении тарифа первый пакет трафика даётся сразу + последующие сбросы.',
       'single'::helpdesk.kb_question_selection_mode, 670, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только то, что в пакете', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только то, что в пакете'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Первый пакет даётся сразу при подключении', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Первый пакет даётся сразу при подключении'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не даётся', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько трафика даётся при подключении тарифа сверх сбросов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не даётся'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?', 'В последний день сброса нет — это учтено в количестве дней (30 дней = 29 сбросов + первый пакет).',
       'single'::helpdesk.kb_question_selection_mode, 680, TRUE,
       ARRAY['sutochnyy-sbros-obnovlenie-trafika']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это ошибка, я передам заявку»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это ошибка, я передам заявку»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это нормально. В последний день сброс не предусмотрен, трафик первого дня компенсирует это»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это нормально. В последний день сброс не предусмотрен, трафик первого дня компенсирует это»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Подключите новый тариф»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что в последний день тарифа нет сброса. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Подключите новый тариф»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое заморозка тарифа?', 'Заморозка — это временная приостановка тарифа. Трафик и срок сохраняются.',
       'single'::helpdesk.kb_question_selection_mode, 690, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое заморозка тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Полное отключение интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Полное отключение интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Приостановка действия тарифа с сохранением остатка трафика и срока', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Приостановка действия тарифа с сохранением остатка трафика и срока'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Удаление учётной записи', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Удаление учётной записи'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда нужна заморозка тарифа?', 'Заморозка для случаев, когда абонент временно не пользуется интернетом (поездка, ремонт).',
       'single'::helpdesk.kb_question_selection_mode, 700, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда нужна заморозка тарифа?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент хочет сменить тариф', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент хочет сменить тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент уезжает и временно не будет пользоваться интернетом', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент уезжает и временно не будет пользоваться интернетом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент недоволен скоростью', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда нужна заморозка тарифа?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент недоволен скоростью'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком при заморозке?', 'При заморозке весь неизрасходованный трафик сохраняется.',
       'single'::helpdesk.kb_question_selection_mode, 710, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сгорает', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сгорает'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик сохраняется и становится доступен после разморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик сохраняется и становится доступен после разморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик переносится на другой тариф', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик переносится на другой тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит со сроком тарифа при заморозке?', 'Срок тарифа приостанавливается на время заморозки.',
       'single'::helpdesk.kb_question_selection_mode, 720, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок продолжает идти', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок продолжает идти'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок приостанавливается на время заморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок приостанавливается на время заморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Срок сокращается вдвое', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит со сроком тарифа при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Срок сокращается вдвое'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Нужно ли отключать текущий тариф перед подключением нового?', 'Для смены тарифа нужно сначала отключить текущий, потом подключить новый.',
       'single'::helpdesk.kb_question_selection_mode, 730, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, старый тариф нужно отключить', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, старый тариф нужно отключить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, новый подключится автоматически', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, новый подключится автоматически'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Нужно ли отключать текущий тариф перед подключением нового?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не может сменить тариф в ЛК. Ваше действие:', 'Сначала попробовать объяснить. Если не получается — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 740, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить пошагово или создать заявку', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить пошагово или создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить тариф через систему', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить тариф через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что смена недоступна', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может сменить тариф в ЛК. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что смена недоступна'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Можно ли подключить тариф, если на балансе недостаточно средств?', 'Для подключения тарифа должно быть достаточно средств на балансе.',
       'single'::helpdesk.kb_question_selection_mode, 750, TRUE,
       ARRAY['smena-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, нужно пополнить баланс', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, нужно пополнить баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, можно в долг', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, можно в долг'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, с последующим списанием', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Можно ли подключить тариф, если на балансе недостаточно средств?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, с последующим списанием'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?', 'Платежи обрабатываются до 30 минут.',
       'single'::helpdesk.kb_question_selection_mode, 760, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 24 часов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько времени могут обрабатываться платежи через ЮMoney/SBP?Money/SBP?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 24 часов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?', 'Если >30 минут — запрашиваем скриншот справки и передаём инженерам для отслеживания.',
       'single'::helpdesk.kb_question_selection_mode, 770, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить подождать ещё', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить подождать ещё'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот справки об операции из приложения банка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот справки об операции из приложения банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пополнить баланс вручную', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Прошло больше 30 минут, деньги не поступили. Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пополнить баланс вручную'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:', 'Автопродление могло подключить тариф — баланс пуст, но тариф активен.',
       'single'::helpdesk.kb_question_selection_mode, 780, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ошибка банка', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ошибка банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сработало автопродление — тариф подключился, деньги на тарифе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сработало автопродление — тариф подключился, деньги на тарифе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги потерялись', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пополнил баланс, деньги списались с карты, но на счёте пусто. Самая частая причина:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги потерялись'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент отправил платёж, но по ошибке указал неправильную сумму:', 'Излишек можно вернуть на баланс через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 790, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не сделать, деньги пропали', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не сделать, деньги пропали'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — инженеры проверят и вернут излишек', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — инженеры проверят и вернут излишек'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить отправить ещё раз', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент отправил платёж, но по ошибке указал неправильную сумму:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить отправить ещё раз'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не может оплатить через СБП — ошибка в системе:', 'Если один способ не работает — предложить альтернативу. Если все не работают — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 800, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что СБП не работает', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что СБП не работает'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить оплатить другим способом (карта, ЮMoney) или создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить оплатить другим способом (карта, ЮMoney) или создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Игнорировать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не может оплатить через СБП — ошибка в системе:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Игнорировать'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент оплатил через банк, чек есть, но деньги не пришли:', 'Запросить скриншот справки об операции из приложения банка',
       'single'::helpdesk.kb_question_selection_mode, 810, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот справки об операции из приложения банка', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот справки об операции из приложения банка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать ждать', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать ждать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил через банк, чек есть, но деньги не пришли:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Срок зачисления платежа на баланс при оплате картой:', 'Платежи обрабатываются до 30 минут.',
       'single'::helpdesk.kb_question_selection_mode, 820, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 30 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 30 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 2 часов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Срок зачисления платежа на баланс при оплате картой:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 2 часов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты', 'Оператор не формирует чеки. Выписку можно получить в банке.',
       'single'::helpdesk.kb_question_selection_mode, 830, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Распечатать и отправить', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Распечатать и отправить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: чек можно получить в своём банке (выписка по операциям)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: чек можно получить в своём банке (выписка по операциям)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на чек', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит чек об оплате. Что делать? Чеки об оплате отправляются абонентам им на почту, но иногда при ошибках в написании почты'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на чек'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?', 'При отрицательном балансе нужно пополнить счёт для подключения тарифа.',
       'single'::helpdesk.kb_question_selection_mode, 840, TRUE,
       ARRAY['oplatil-no-dengi-ne-prishli']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пополнить баланс', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пополнить баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку для разблокировки', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку для разблокировки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подождать автоматического списания', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Баланс абонента в минусе, интернет не работает. Что нужно сделать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подождать автоматического списания'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кто принимает решение о возврате денег?', 'Возвраты и компенсации — только через заявку, решение принимают инженеры.',
       'single'::helpdesk.kb_question_selection_mode, 850, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кто принимает решение о возврате денег?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператор контакт-центра', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператор контакт-центра'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только инженеры', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только инженеры'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кто принимает решение о возврате денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит вернуть деньги на карту, а не на баланс:', 'Вывод на карту возможен, но по решению инженеров. Только заявка.',
       'single'::helpdesk.kb_question_selection_mode, 860, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Такой возможности нет', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Такой возможности нет'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Можно, но по решению инженеров через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Можно, но по решению инженеров через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть может только оператор', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит вернуть деньги на карту, а не на баланс:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть может только оператор'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужны для заявки на возврат?', 'В заявке должны быть ID абонента, период и причина возврата.',
       'single'::helpdesk.kb_question_selection_mode, 870, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, период и причина возврата', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, период и причина возврата'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только сумма', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужны для заявки на возврат?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только сумма'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент заплатил за тариф, но передумал через 5 минут:', 'Если абонент не пользовался — возможен возврат на баланс через заявку.',
       'single'::helpdesk.kb_question_selection_mode, 880, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги не возвращаются', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги не возвращаются'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку — если трафик не израсходован, возможен возврат на баланс', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку — если трафик не израсходован, возможен возврат на баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вернуть деньги сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент заплатил за тариф, но передумал через 5 минут:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вернуть деньги сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда абоненту НЕ положен возврат денег?', 'Если абонент сам потратил трафик — возврат не положен.',
       'single'::helpdesk.kb_question_selection_mode, 890, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Была проблема на нашей стороне', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Была проблема на нашей стороне'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент сам израсходовал весь трафик и хочет деньги назад', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент сам израсходовал весь трафик и хочет деньги назад'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Двойное списание по нашей ошибке', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда абоненту НЕ положен возврат денег?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Двойное списание по нашей ошибке'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Возврат на карту осуществляется:', 'Только инженеры принимают решение о выводе средств на карту.',
       'single'::helpdesk.kb_question_selection_mode, 900, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Возврат на карту осуществляется:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'По решению инженеров', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'По решению инженеров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Мгновенно оператором', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Возврат на карту осуществляется:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Мгновенно оператором'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?', 'Компенсируется время фактического простоя, зафиксированное системой.',
       'single'::helpdesk.kb_question_selection_mode, 910, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Весь период тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Весь период тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только время, когда была зафиксирована проблема', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только время, когда была зафиксирована проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Не компенсируется', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Компенсация за простой (когда интернет не работал по нашей вине) — какой период компенсируется?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Не компенсируется'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Куда возвращаются средства при компенсации?', 'При компенсации средства возвращаются на баланс ЛК, не на карту.',
       'single'::helpdesk.kb_question_selection_mode, 920, TRUE,
       ARRAY['trebovanie-vozvrata-deneg']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На карту абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На карту абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На баланс личного кабинета', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На баланс личного кабинета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Наличными', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Куда возвращаются средства при компенсации?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Наличными'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'С чего начинается работа с обращением «нет интернета»?', 'Диагностика — первый шаг. Она проверит 6 параметров.',
       'single'::helpdesk.kb_question_selection_mode, 930, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сразу создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сразу создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запустить диагностику в карточке абонента', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запустить диагностику в карточке абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить перезагрузить роутер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С чего начинается работа с обращением «нет интернета»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить перезагрузить роутер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?', 'Если диагностика не показывает проблему — передаём заявку с данными.',
       'single'::helpdesk.kb_question_selection_mode, 940, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Попросить подождать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Попросить подождать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Собрать данные (ID, устройство, тип подключения) и создать заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Собрать данные (ID, устройство, тип подключения) и создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перезагрузить систему', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает, что всё зелёное, но интернета нет. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перезагрузить систему'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое кнопка «Диагностика» в карточке абонента?', 'Диагностика проверяет: учётная запись, тариф, баланс, станция, сессия, лимит сессий.',
       'single'::helpdesk.kb_question_selection_mode, 950, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Кнопка перезагрузки оборудования', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Кнопка перезагрузки оборудования'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматическая проверка 6 параметров учётной записи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматическая проверка 6 параметров учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создание заявки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое кнопка «Диагностика» в карточке абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создание заявки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Результат диагностики — это:', 'Диагностика — инструмент оператора. Абоненту не нужно знать её результат, ему нужен срок решения.',
       'single'::helpdesk.kb_question_selection_mode, 960, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Результат диагностики — это:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответ для абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответ для абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Инструмент для оператора, чтобы понять причину', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Инструмент для оператора, чтобы понять причину'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отчёт для инженеров', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Результат диагностики — это:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отчёт для инженеров'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Рабочее время инженеров для обработки заявок:', 'Инженеры работают с 8:00 до 16:00 по московскому времени в будние дни.',
       'single'::helpdesk.kb_question_selection_mode, 970, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Круглосуточно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Круглосуточно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8:00–16:00 МСК в будни', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8:00–16:00 МСК в будни'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '9:00–18:00 МСК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Рабочее время инженеров для обработки заявок:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '9:00–18:00 МСК'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?', 'Вечером и в выходные — ответ в начале следующего рабочего дня.',
       'single'::helpdesk.kb_question_selection_mode, 980, TRUE,
       ARRAY['net-podklyucheniya-k-internetu']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через 15 минут', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующего рабочего дня (понедельник)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующего рабочего дня (понедельник)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В субботу днём', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если заявка подана инженерам в 20:00 в пятницу — когда ждать ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В субботу днём'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие сроки ответа инженеров на заявку в рабочее время?', 'В рабочее время (8:00–16:00 МСК, будни) ответ — до 15 минут.',
       'single'::helpdesk.kb_question_selection_mode, 990, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 1 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 1 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 15 минут', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'До 10 минут', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие сроки ответа инженеров на заявку в рабочее время?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'До 10 минут'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Заявка подана в воскресенье вечером. Когда ответ?', 'Вечером, в выходные и праздники — ответ в начале следующего рабочего дня.',
       'single'::helpdesk.kb_question_selection_mode, 1000, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через 15 минут', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через 15 минут'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующего рабочего дня (понедельник)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующего рабочего дня (понедельник)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В воскресенье ночью', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Заявка подана в воскресенье вечером. Когда ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В воскресенье ночью'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?', 'Если не работает только конкретный ресурс — скорее всего блокировка РКН.',
       'single'::helpdesk.kb_question_selection_mode, 1010, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проблема с его тарифом', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проблема с его тарифом'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Вероятно, блокировка РКН', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Вероятно, блокировка РКН'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проблема с оборудованием', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется, что WhatsApp не работает. Другие сайты открываются. Что это?WhatsApp не работает. Другие сайты открываются. Что это?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проблема с оборудованием'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Может ли оператор повлиять на блокировку РКН?', 'РКН-блокировки — не наша ответственность. Только консультация.',
       'single'::helpdesk.kb_question_selection_mode, 1020, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, через заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, это требование законодательства, мы не влияем', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, это требование законодательства, мы не влияем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Может, но только для некоторых сайтов', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Может ли оператор повлиять на блокировку РКН?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Может, но только для некоторых сайтов'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:', 'Если работает всё, кроме одного ресурса — это блокировка/замедление РКН.',
       'single'::helpdesk.kb_question_selection_mode, 1030, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку, инженеры проверят»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку, инженеры проверят»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Возможно, это замедление/блокировка РКН. Мы не можем на это повлиять»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Возможно, это замедление/блокировка РКН. Мы не можем на это повлиять»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Проверьте скорость интернета»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «YouTube тормозит, все остальные сайты работают». Ваш ответ:YouTube тормозит, все остальные сайты работают». Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Проверьте скорость интернета»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'При РКН-блокировке оператор:', 'Это не техническая проблема. Только консультация абонента.',
       'single'::helpdesk.kb_question_selection_mode, 1040, TRUE,
       ARRAY['rkn-blokirovki-i-ogranicheniya-dostupa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'При РКН-блокировке оператор:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создаёт заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создаёт заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Даёт консультацию, заявка не создаётся', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Даёт консультацию, заявка не создаётся'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перенаправляет к менеджеру', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'При РКН-блокировке оператор:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перенаправляет к менеджеру'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент просит точное время ответа инженеров. Что ответить?', 'Всегда называть конкретный срок. «Скоро» — худший вариант.',
       'single'::helpdesk.kb_question_selection_mode, 1050, TRUE,
       ARRAY['sroki-otveta-inzhenerov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я не знаю точно, сколько ждать»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я не знаю точно, сколько ждать»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«В рабочее время — до 15 минут. Вечером/в выходные — в начале следующего рабочего дня»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«В рабочее время — до 15 минут. Вечером/в выходные — в начале следующего рабочего дня»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ждите, вам ответят»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент просит точное время ответа инженеров. Что ответить?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ждите, вам ответят»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое MAC-адрес?MAC-адрес?', 'MAC-адрес — уникальный идентификатор сетевого устройства, 12 символов.',
       'single'::helpdesk.kb_question_selection_mode, 1060, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Физический адрес устройства (роутера, телефона) — 12 символов', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Физический адрес устройства (роутера, телефона) — 12 символов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Модель роутера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое MAC-адрес?MAC-адрес?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Модель роутера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?', 'Принципиально разные типы подключения. HOTSPOT — ввод данных в браузере. PPPoE — в настройках роутера.',
       'single'::helpdesk.kb_question_selection_mode, 1070, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только названием, это одно и то же', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только названием, это одно и то же'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT — через браузер, сессия активна пока устройство онлайн. PPPoE — «зашит» в роутер, сессия всегда активна', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT — через браузер, сессия активна пока устройство онлайн. PPPoE — «зашит» в роутер, сессия всегда активна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT быстрее', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Чем отличается HOTSPOT от PPPoE?HOTSPOT от PPPoE?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT быстрее'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое «лимит сессий»?', 'Лимит сессий — это ограничение на количество одновременно подключённых устройств.',
       'single'::helpdesk.kb_question_selection_mode, 1080, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое «лимит сессий»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальная скорость интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальная скорость интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальное количество устройств, которые могут быть онлайн одновременно', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальное количество устройств, которые могут быть онлайн одновременно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Максимальный расход трафика', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «лимит сессий»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Максимальный расход трафика'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Когда снимается ограничение скорости?', 'Скорость восстанавливается после сброса трафика или Турбо-кнопки.',
       'single'::helpdesk.kb_question_selection_mode, 1090, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Когда снимается ограничение скорости?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через час', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через час'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'После суточного сброса или подключения Турбо-кнопки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'После суточного сброса или подключения Турбо-кнопки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'При перезагрузке роутера', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Когда снимается ограничение скорости?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'При перезагрузке роутера'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое ID абонента?ID абонента?', 'ID — уникальный номер учётной записи. Он же логин для входа в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 1100, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пароль от ЛК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пароль от ЛК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Уникальный номер учётной записи, логин для входа', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Уникальный номер учётной записи, логин для входа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Номер телефона', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое ID абонента?ID абонента?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Номер телефона'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Для чего нужна кнопка «Диагностика»?', 'Диагностика проверяет: учётная запись, тариф, баланс, станция, сессия, лимит.',
       'single'::helpdesk.kb_question_selection_mode, 1110, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для создания заявки', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для создания заявки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для проверки 6 параметров учётной записи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для проверки 6 параметров учётной записи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Для отправки уведомления', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Для чего нужна кнопка «Диагностика»?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Для отправки уведомления'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?', 'PPPoE — настройки прописаны в роутере, подключается автоматически.',
       'single'::helpdesk.kb_question_selection_mode, 1120, TRUE,
       ARRAY['glossariy-terminov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'HOTSPOT', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'HOTSPOT'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'PPPoE', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'PPPoE'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'VPN', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип подключения используется, если роутер настраивается один раз и потом подключается сам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'VPN'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?', 'Самая частая причина — автообновления приложений и ОС, синхронизация облака.',
       'single'::helpdesk.kb_question_selection_mode, 1130, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Кто-то украл пароль', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Кто-то украл пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Фоновые обновления приложений', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Фоновые обновления приложений'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбой системы', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Я ничего не делал, а трафик закончился». Какая причина самая вероятная?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбой системы'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как помочь абоненту проверить, куда уходит трафик?', 'Мы не видим, на какие приложения тратится трафик. Только на устройстве или через GlassWire.',
       'single'::helpdesk.kb_question_selection_mode, 1140, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть на нашей стороне', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть на нашей стороне'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Порекомендовать установить GlassWire или проверить «Передачу данных» в настройках телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Порекомендовать установить GlassWire или проверить «Передачу данных» в настройках телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как помочь абоненту проверить, куда уходит трафик?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?', 'При отсутствии мобильной связи — только восстановление через почту.',
       'single'::helpdesk.kb_question_selection_mode, 1150, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только через почту', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только через почту'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через звонок робота', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через звонок робота'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Никак', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент в отдалённом посёлке, мобильной связи нет. Как ему восстановить пароль?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Никак'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?', 'Для PPPoE логин/пароль «зашиты» в роутер. При смене — заявка инженерам.',
       'single'::helpdesk.kb_question_selection_mode, 1160, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что новые настройки нужны в роутере — заявка инженерам', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что новые настройки нужны в роутере — заявка инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать купить другой роутер', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать купить другой роутер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключить через HOTSPOT', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент поменял роутер и не может подключиться (PPPoE). Что делать?PPPoE). Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключить через HOTSPOT'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:', 'Абоненты часто не отвечают, потому что не узнают номер. Предупредите заранее.',
       'single'::helpdesk.kb_question_selection_mode, 1170, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предупредить заранее: «Вам позвонит робот с неизвестного номера — пожалуйста, ответьте»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предупредить заранее: «Вам позвонит робот с неизвестного номера — пожалуйста, ответьте»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это его проблема', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не отвечает на звонки робота при восстановлении пароля. Ваше действие:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это его проблема'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?', 'Объяснить причину, заморозить тариф',
       'single'::helpdesk.kb_question_selection_mode, 1180, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это не наша проблема', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это не наша проблема'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: оборудование не работает без электричества. Заморозить тариф', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: оборудование не работает без электричества. Заморозить тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать компенсацию', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат: «Сижу без интернета третий день из-за погоды/отключения света». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать компенсацию'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»', 'Сначала уточнить — все устройства или одно. Если все — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 1190, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это нормально', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это нормально'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить: одно устройство или все? Если одно — проблема устройства. Если все — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить: одно устройство или все? Если одно — проблема устройства. Если все — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку сразу', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент говорит: «Интернет каждые 5 минут отключается — что делать?»'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку сразу'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?', 'Самый простой способ — сменить пароль от Wi-Fi в ЛК. Все старые подключения сбросятся.',
       'single'::helpdesk.kb_question_selection_mode, 1200, TRUE,
       ARRAY['lichnyy-kabinet-i-dostup']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сменить пароль', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сменить пароль'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет проверить, не подключено ли чужое устройство к его Wi-Fi. Что посоветовать?Wi-Fi. Что посоветовать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент не знает свой логин для входа. Что делать?', 'Логин (ID) виден в карточке абонента.',
       'single'::helpdesk.kb_question_selection_mode, 1210, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать новую учётную запись', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать новую учётную запись'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в карточке (ID) и сообщить', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в карточке (ID) и сообщить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сбросить ЛК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент не знает свой логин для входа. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сбросить ЛК'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Диагностика показывает: «Лимит сессий превышен». Что делать?', 'Лимит сессий можно сбросить в ЛК или помочь и сбросить в системе',
       'single'::helpdesk.kb_question_selection_mode, 1220, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего, это проблема абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего, это проблема абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что превышен лимит устройств. Попросить сбросить сессии в ЛК или помочь и сбросить их в системе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что превышен лимит устройств. Попросить сбросить сессии в ЛК или помочь и сбросить их в системе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Диагностика показывает: «Лимит сессий превышен». Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?', 'Замедление конкретных ресурсов — не техническая проблема, а блокировка РКН.',
       'single'::helpdesk.kb_question_selection_mode, 1230, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это проблема вашего интернета»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это проблема вашего интернета»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Возможно, замедление/блокировка РКН. Мы не можем на это повлиять»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Возможно, замедление/блокировка РКН. Мы не можем на это повлиять»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Создам заявку инженерам»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент утверждает, что WhatsApp работает, но медленно загружает видео. Ваш ответ?WhatsApp работает, но медленно загружает видео. Ваш ответ?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Создам заявку инженерам»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:', 'Мы не знаем и не можем комментировать сроки снятия блокировок РКН.',
       'single'::helpdesk.kb_question_selection_mode, 1240, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Завтра»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Завтра»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это решается на государственном уровне, у нас нет такой информации»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это решается на государственном уровне, у нас нет такой информации»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Через неделю»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Когда снимут блокировку с Telegram/YouTube?» Ваш ответ:Telegram/YouTube?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Через неделю»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое «сессия» простыми словами?', 'Сессия — это подключение устройства к сети. Одно устройство = одна сессия.',
       'single'::helpdesk.kb_question_selection_mode, 1250, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое «сессия» простыми словами?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Время работы интернета', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Время работы интернета'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Подключение одного устройства к сети', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Подключение одного устройства к сети'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость интернета', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое «сессия» простыми словами?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость интернета'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?', 'Погода (ветер, снег) может влиять на спутниковое оборудование. Если временно — объяснить. Если постоянно — заявка.',
       'single'::helpdesk.kb_question_selection_mode, 1260, TRUE,
       ARRAY['problemy-s-oborudovaniem']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на ремонт', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на ремонт'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить: погода может влиять на спутниковую связь. Если проблема повторится — заявка', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить: погода может влиять на спутниковую связь. Если проблема повторится — заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего не делать', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент жалуется на погодные условия — говорит, интернет пропадает. Что делать?погодные условия — говорит, интернет пропадает. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего не делать'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:', 'Не сравнивать тарифы абонентов. Перенаправить к информации на сайте/в ЛК.',
       'single'::helpdesk.kb_question_selection_mode, 1270, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«У всех такие же»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«У всех такие же»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Цены можно посмотреть на сайте и в ЛК. Если у вас есть вопросы по тарифу — я могу помочь»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Цены можно посмотреть на сайте и в ЛК. Если у вас есть вопросы по тарифу — я могу помочь»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Это секретная информация»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Подскажите, у всех такие тарифы или только у меня дорогие?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Это секретная информация»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент кричит и оскорбляет оператора. Ваше действие?', 'Не принимать на свой счёт. ────────────────────────────────────────────────────────────────────────────────',
       'single'::helpdesk.kb_question_selection_mode, 1280, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответить тем же', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответить тем же'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Спокойно выслушать, не принимать на свой счёт.', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Спокойно выслушать, не принимать на свой счёт.'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Положить трубку', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент кричит и оскорбляет оператора. Ваше действие?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Положить трубку'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как лучше начать диалог с раздражённым абонентом?', 'Сразу переводить в конструктив — предложить конкретное действие.',
       'single'::helpdesk.kb_question_selection_mode, 1290, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Слушаю вас, чем могу помочь?»', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Слушаю вас, чем могу помочь?»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Здравствуйте! Давайте я проверю по вашей учётной записи, что можно сделать»', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Здравствуйте! Давайте я проверю по вашей учётной записи, что можно сделать»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Не волнуйтесь, сейчас всё решим»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как лучше начать диалог с раздражённым абонентом?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Не волнуйтесь, сейчас всё решим»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:', 'Заявка на добавление контента. Решение за инженерами.',
       'single'::helpdesk.kb_question_selection_mode, 1300, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Я передам запрос инженерам» — заявка с названием контента', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Я передам запрос инженерам» — заявка с названием контента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Фильмы загружаются автоматически»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Фильмы загружаются автоматически»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Ищите в других сервисах»', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает: «Почему в Мультикасте нет свежих фильмов?» Ваш ответ:Мультикасте нет свежих фильмов?» Ваш ответ:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Ищите в других сервисах»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Как часто обновляется контент на Мультикасте?Мультикасте?', 'Оператор не управляет контентом Мультикаста. Вопросы по контенту — в заявку.',
       'single'::helpdesk.kb_question_selection_mode, 1310, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Каждый день', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Каждый день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Эту информацию оператор не знает. Запрос на обновление — через заявку', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Эту информацию оператор не знает. Запрос на обновление — через заявку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Раз в неделю', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Как часто обновляется контент на Мультикасте?Мультикасте?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Раз в неделю'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?', 'Ситуация 2 — «Не было доступа к сети»',
       'single'::helpdesk.kb_question_selection_mode, 1320, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это неизрасходованный трафик — инженеры проверят остаток и восстановят', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это неизрасходованный трафик — инженеры проверят остаток и восстановят'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это «не было доступа к сети» — уточнить даты, создать заявку инженерам. Они проверят расход трафика за эти дни и, если его не было, продлят тариф', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это «не было доступа к сети» — уточнить даты, создать заявку инженерам. Они проверят расход трафика за эти дни и, если его не было, продлят тариф'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Это автопродление — создать заявку на возврат средств', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «26, 27, 28 апреля не было сигнала. Прошу продлить срок действия тарифа». Какой это тип обращения и что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Это автопродление — создать заявку на возврат средств'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?', 'Ситуация 1 + Главное правило',
       'single'::helpdesk.kb_question_selection_mode, 1330, TRUE,
       ARRAY['voprosy-po-spisaniyam-i-rashodam']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, оператор может самостоятельно восстановить остаток через систему', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, оператор может самостоятельно восстановить остаток через систему'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, оператор не восстанавливает трафик самостоятельно. Нужно объяснить абоненту, что информация передана специалистам, и создать заявку инженерам', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, оператор не восстанавливает трафик самостоятельно. Нужно объяснить абоненту, что информация передана специалистам, и создать заявку инженерам'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, остаток сгорает, и абоненту нужно купить новый тариф', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент оплатил Слайдер тариф, но не потратил весь объём — осталось 300 МБ. Он просит их вернуть. Оператор может самостоятельно подключить остаток?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, остаток сгорает, и абоненту нужно купить новый тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?', 'Раздел «Когда ждать ответа от инженеров» — после 16:00 до следующего рабочего дня',
       'single'::helpdesk.kb_question_selection_mode, 1340, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«В течение 15 минут» — это рабочее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«В течение 15 минут» — это рабочее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Инженеры ответят в течение 8 часов»', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Инженеры ответят в течение 8 часов»'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '«Уже вечер пятницы, поэтому заявку рассмотрят в начале следующей рабочей недели»', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет в чат в 19:00 в пятницу по московскому времени: «Три дня не было интернета, продлите тариф». Когда оператору сказать, что инженеры ответят?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '«Уже вечер пятницы, поэтому заявку рассмотрят в начале следующей рабочей недели»'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?', 'Ситуация 1 - «Заморозьте тариф». Оператор сначала предлагает сделать это самостоятельно в ЛК. Если не получается - заявка инженерам. Диктовать телефон инженера абоненту запрещено.',
       'single'::helpdesk.kb_question_selection_mode, 1350, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам на заморозку', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам на заморозку'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить абоненту заморозить тариф самостоятельно в личном кабинете (вкладка «Тарифы»)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить абоненту заморозить тариф самостоятельно в личном кабинете (вкладка «Тарифы»)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что заморозка больше недоступна', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что заморозка больше недоступна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Передать номер телефона инженера абоненту', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, заморозьте тариф, так как я в отъезде». Что должен сделать оператор в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Передать номер телефона инженера абоненту'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько раз за один тариф можно воспользоваться функцией заморозки?', 'Функция заморозки даётся один раз за весь тариф. Заморозка + разморозка = одно использование. Это ключевое ограничение.',
       'single'::helpdesk.kb_question_selection_mode, 1360, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Неограниченное количество раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Неограниченное количество раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '2 раза', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '2 раза'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '1 раз', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '1 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '3 раза', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько раз за один тариф можно воспользоваться функцией заморозки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '3 раза'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с тарифом при заморозке?', 'Заморозка останавливает действие тарифа, но сохраняет текущие дни и объём трафика. При разморозке тариф возобновляется с того же места.',
       'single'::helpdesk.kb_question_selection_mode, 1370, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф сгорает, деньги возвращаются на баланс', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф сгорает, деньги возвращаются на баланс'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф полностью отключается, оставшиеся дни и трафик аннулируются', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф полностью отключается, оставшиеся дни и трафик аннулируются'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф останавливается, оставшиеся дни и объём трафика сохраняются до разморозки', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф останавливается, оставшиеся дни и объём трафика сохраняются до разморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф продолжает действовать, но скорость снижается', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с тарифом при заморозке?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф продолжает действовать, но скорость снижается'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?', 'Ситуация 4 - «Заморозка при проблемах с сетью». Если проблема на стороне провайдера, инженеры сами решают. Создаётся заявка.',
       'single'::helpdesk.kb_question_selection_mode, 1380, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отказать, так как заморозка даётся только 1 раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отказать, так как заморозка даётся только 1 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Предложить заморозить через ЛК и скинуть инструкцию', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Предложить заморозить через ЛК и скинуть инструкцию'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам с указанием причины «проблемы с сетью», так как в таких случаях инженеры сами решают вопрос с заморозкой', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам с указанием причины «проблемы с сетью», так как в таких случаях инженеры сами решают вопрос с заморозкой'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посоветовать абоненту купить новый тариф', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит и говорит, что интернет не работает из-за проблем на станции, и просит заморозить тариф. Что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посоветовать абоненту купить новый тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?', 'Если абонент просит заморозить с определённой даты, нужно передать конкретную дату в заявку вместе с ID абонента.',
       'single'::helpdesk.kb_question_selection_mode, 1390, TRUE,
       ARRAY['zamorozka-razmorozka-tarifa']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID абонента', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID абонента'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента и желаемую дату заморозки', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента и желаемую дату заморозки'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только желаемую дату', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только желаемую дату'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ничего, заморозка действует с момента подачи заявки', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент хочет заморозить тариф с определённой даты - например, «заморозьте с 20 июня». Что передать в заявку?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ничего, заморозка действует с момента подачи заявки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?', 'Ситуация 2. Сначала чек и проверка в системе.',
       'single'::helpdesk.kb_question_selection_mode, 1400, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку на возврат в бухгалтерию', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку на возврат в бухгалтерию'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Запросить скриншот чека, проверить в системе', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Запросить скриншот чека, проверить в системе'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать - ошибка банка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'С карты списали 5700, абонент не понимает за что. Что делать в первую очередь?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать - ошибка банка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Пополнил на 1000, на счету 150. Что могло произойти?', 'Ситуация 1. Автопродление - главная причина. Либо домочадцы.',
       'single'::helpdesk.kb_question_selection_mode, 1410, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ошибка - срочная заявка', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ошибка - срочная заявка'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Проверить активно ли автопродление', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Проверить активно ли автопродление'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Комиссия банка 850', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Пополнил на 1000, на счету 150. Что могло произойти?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Комиссия банка 850'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Списание с карты не отображается в системе. Что передать инженерам?', 'Нужен полный комплект: ID, дата, время, сумма, чек, комментарий.',
       'single'::helpdesk.kb_question_selection_mode, 1420, TRUE,
       ARRAY['voprosy-po-spisaniyam-i-rashodam']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только ID', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только ID'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID, дату/время, сумму, скриншот чека с комментарием', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID, дату/время, сумму, скриншот чека с комментарием'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только скриншот', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Списание с карты не отображается в системе. Что передать инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только скриншот'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?', 'Ситуация 1 - «Почему трафик не обновился?». Причины: последний день тарифа, закончились сбросы (сбросов = дней минус 1). Варианта «не подтвердил списание» не существует.',
       'single'::helpdesk.kb_question_selection_mode, 1430, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сегодня последний день действия тарифа - суточный сброс не предусмотрен', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сегодня последний день действия тарифа - суточный сброс не предусмотрен'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Количество сбросов уже исчерпано (сбросов = количество дней минус 1)', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Количество сбросов уже исчерпано (сбросов = количество дней минус 1)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент забыл подтвердить списание в личном кабинете', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Здравствуйте, почему трафик не обновился? У меня должно было в 17:00 обновиться». Что из перечисленного НЕ является причиной отсутствия сброса?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент забыл подтвердить списание в личном кабинете'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?', 'Ситуация 2 - «Во сколько обновляется трафик?». Время сброса каждый абонент выбирает сам при подключении, поэтому у всех оно разное. Оператор смотрит в системе и сообщает.',
       'single'::helpdesk.kb_question_selection_mode, 1440, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что у всех абонентов сброс в 00:00 по МСК', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что у всех абонентов сброс в 00:00 по МСК'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Посмотреть в системе время сброса для этого абонента и сообщить по МСК (и по местному, если нужно)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Посмотреть в системе время сброса для этого абонента и сообщить по МСК (и по местному, если нужно)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам, чтобы они узнали время сброса', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам, чтобы они узнали время сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ответить, что время сброса оператору недоступно', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент спрашивает во сколько у него обновляется трафик. Что должен сделать оператор?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ответить, что время сброса оператору недоступно'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?', 'Ситуация 4 - «Трафик быстро закончился после сброса». Система видит общий расход, но не знает, на какие приложения. Рекомендуем установить GlassWire или проверить настройки телефона - раздел «Передача данных».',
       'single'::helpdesk.kb_question_selection_mode, 1450, TRUE,
       ARRAY['kuda-uhodit-trafik']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку инженерам на возврат трафика', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку инженерам на возврат трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Объяснить, что трафик мог быть потрачен фоновыми приложениями, и порекомендовать приложение для учёта трафика (GlassWire), а также “Передача данных” в настройках телефона', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Объяснить, что трафик мог быть потрачен фоновыми приложениями, и порекомендовать приложение для учёта трафика (GlassWire), а также “Передача данных” в настройках телефона'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что это ошибка системы, и подключить новый пакет вручную', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что это ошибка системы, и подключить новый пакет вручную'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Перенаправить абонента в службу технической поддержки', FALSE, 30
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент пишет: «Только обновилось и уже 0 МБ - я вообще не пользовался, куда всё делось?». Что делать оператору?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Перенаправить абонента в службу технической поддержки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?', 'Раздел «Когда ждать ответа от инженеров». С 8:00 до 16:00 в будни по МСК - 15 минут. Остальное время, выходные и праздники - до следующего рабочего дня. 17:30 пятницы - уже не рабочее время.',
       'single'::helpdesk.kb_question_selection_mode, 1460, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В течение 15 минут - это рабочее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В течение 15 минут - это рабочее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В течение часа', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В течение часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'В начале следующей рабочей недели (после 16:00 в будни - до следующего рабочего дня)', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент звонит в 17:30 в пятницу по МСК и просит изменить время сброса. Когда примерно можно ждать ответа от инженеров?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'В начале следующей рабочей недели (после 16:00 в будни - до следующего рабочего дня)'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?', 'Ситуация 1 - количество сбросов = количество дней минус 1. Первый пакет даётся при подключении, дальше каждый день - по одному сбросу. 7 дней = 6 сбросов + первый пакет при подключении.',
       'single'::helpdesk.kb_question_selection_mode, 1470, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '7 раз', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '7 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '6 раз', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '6 раз'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '8 раз', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Абонент подключил тариф на 7 дней. Сколько раз за время тарифа произойдёт суточный сброс?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '8 раз'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В каких случаях оператор должен создать заявку инженерам?', 'Общий принцип из памятки: «если у абонента остались вопросы и доводы КЦ не работают - оператор создаёт заявку инженерам». Также заявка обязательна при смене времени сброса.',
       'single'::helpdesk.kb_question_selection_mode, 1480, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент спрашивает время сброса', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент спрашивает время сброса'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если абонент жалуется на быстрый расход трафика', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если абонент жалуется на быстрый расход трафика'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Если у абонента остались вопросы и доводы КЦ не работают, или если требуется изменить время сброса', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях оператор должен создать заявку инженерам?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Если у абонента остались вопросы и доводы КЦ не работают, или если требуется изменить время сброса'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что такое турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 1490, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что такое турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продление тарифа на новый срок', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продление тарифа на новый срок'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Платная опция, которая восстанавливает суточный лимит трафика на безлимитных тарифах, также восстанавливает скорость из ограничения скорости до скорости по тарифу', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Платная опция, которая восстанавливает суточный лимит трафика на безлимитных тарифах, также восстанавливает скорость из ограничения скорости до скорости по тарифу'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Смена тарифа на слайдер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что такое турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Смена тарифа на слайдер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Сколько стоит турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 1500, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Зависит от тарифа — от 50 до 300 ₽', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Зависит от тарифа — от 50 до 300 ₽'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '160 ₽ — фиксированная цена Зависит от объёма суточного пакета трафика, например цена турбо-кнопки для тарифа Безлимитный 300 стоит 180р., а для тарифа Безлимитный 1500 стоит 540р.. Уточню, что стоимость турбок-нопки это стоимость суточного тариф с таким же объёмом трафика, например турбо-кнопка для тарифа Безлимитный 300 на 30 суток стоит 180р. как и тариф Безлимитный 300 на 1 день', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '160 ₽ — фиксированная цена Зависит от объёма суточного пакета трафика, например цена турбо-кнопки для тарифа Безлимитный 300 стоит 180р., а для тарифа Безлимитный 1500 стоит 540р.. Уточню, что стоимость турбок-нопки это стоимость суточного тариф с таким же объёмом трафика, например турбо-кнопка для тарифа Безлимитный 300 на 30 суток стоит 180р. как и тариф Безлимитный 300 на 1 день'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, '100 ₽', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Сколько стоит турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = '100 ₽'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'На каких тарифах доступна турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 1510, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только на безлимитных тарифах', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только на безлимитных тарифах'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'На всех тарифах, включая слайдер', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'На всех тарифах, включая слайдер'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только на слайдер-тарифах', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На каких тарифах доступна турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только на слайдер-тарифах'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что делает турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 1520, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что делает турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Продлевает тариф на 24 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Продлевает тариф на 24 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Восстанавливает суточный лимит трафика, который выбрал абонент, также восстанавливает скорость из ограничения скорости до скорости по тарифу', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Восстанавливает суточный лимит трафика, который выбрал абонент, также восстанавливает скорость из ограничения скорости до скорости по тарифу'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Добавляет 500 МБ трафика независимо от тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что делает турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Добавляет 500 МБ трафика независимо от тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?', '',
       'single'::helpdesk.kb_question_selection_mode, 1530, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что это техническое ограничение системы', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что это техническое ограничение системы'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Чтобы абонент не платил, когда трафик ещё есть — защита от лишних трат', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Чтобы абонент не платил, когда трафик ещё есть — защита от лишних трат'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Потому что кнопка активируется только раз в сутки', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Почему при остатке пакета больше 80 % турбо-кнопка недоступна?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Потому что кнопка активируется только раз в сутки'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Турбо-кнопка продлевает тариф?', '',
       'single'::helpdesk.kb_question_selection_mode, 1540, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, на 24 часа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, на 24 часа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Да, до конца месяца', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Да, до конца месяца'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Нет, она только восстанавливает дневной лимит, но не продлевает тариф', TRUE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Турбо-кнопка продлевает тариф?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Нет, она только восстанавливает дневной лимит, но не продлевает тариф'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 1550, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что турбо-кнопка бесплатна', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что турбо-кнопка бесплатна'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что турбо-кнопка не продлевает тариф, а только восстанавливает дневной лимит', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что турбо-кнопка не продлевает тариф, а только восстанавливает дневной лимит'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Что после подключения тариф автоматически продлится', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что нужно обязательно сказать абоненту перед подключением турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Что после подключения тариф автоматически продлится'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 1560, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик турбо-кнопки сохранится до следующего подключения тарифа', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик турбо-кнопки сохранится до следующего подключения тарифа'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Трафик турбо-кнопки сгорит вместе с тарифом. Инженеры могут компенсировать стоимость', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Трафик турбо-кнопки сгорит вместе с тарифом. Инженеры могут компенсировать стоимость'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Деньги автоматически вернутся на баланс', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что произойдёт, если тариф закончится сразу после покупки турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Деньги автоматически вернутся на баланс'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?', '',
       'single'::helpdesk.kb_question_selection_mode, 1570, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента, скриншот чека и адрес', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента, скриншот чека и адрес'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ID абонента с пометкой о компенсации', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ID абонента с пометкой о компенсации'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только название тарифа', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные передать инженерам, если требуется компенсация турбо-кнопки?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только название тарифа'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'В каких случаях применяется турбо-кнопка?', '',
       'single'::helpdesk.kb_question_selection_mode, 1580, TRUE,
       ARRAY['kak-sobrat-dannye-dlya-zayavki']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф активен, трафик закончился, остаток пакета меньше 80 %', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф активен, трафик закончился, остаток пакета меньше 80 %'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Тариф закончился, нужно продлить', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Тариф закончился, нужно продлить'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонент хочет сменить тариф на другой', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'В каких случаях применяется турбо-кнопка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонент хочет сменить тариф на другой'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком на лимитном тарифе после его исчерпания?', 'На лимитных тарифах при исчерпании трафика доступ приостанавливается. Продление — за 50-100 ₽.',
       'single'::helpdesk.kb_question_selection_mode, 1590, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость падает до 128 Кбит/с', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость падает до 128 Кбит/с'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доступ приостанавливается', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доступ приостанавливается'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически подключается Турбо-кнопка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на лимитном тарифе после его исчерпания?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически подключается Турбо-кнопка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?', 'На безлимитных тарифах при превышении дневного лимита скорость падает до 128 Кбит/с. В полночь пакет обновляется.',
       'single'::helpdesk.kb_question_selection_mode, 1600, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Доступ приостанавливается до полуночи', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Доступ приостанавливается до полуночи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Скорость падает до 128 Кбит/с до полуночи', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Скорость падает до 128 Кбит/с до полуночи'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически списываются деньги', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Что происходит с трафиком на безлимитном тарифе при превышении дневного лимита?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически списываются деньги'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?', 'Лимитные тарифы — это покупка фиксированного объёма трафика (от 1000 до 100000 МБ). После исчерпания доступ приостанавливается.',
       'single'::helpdesk.kb_question_selection_mode, 1610, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Безлимитный', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Безлимитный'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Лимитный', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Лимитный'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Турбо-кнопка', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тариф подходит для абонента, который хочет купить большой объём трафика сразу и не платить ежемесячно?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Турбо-кнопка'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?', 'Безлимитные тарифы — ежедневное обновление пакета трафика. Подходят для активных пользователей.',
       'single'::helpdesk.kb_question_selection_mode, 1620, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Лимитные', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Лимитные'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Безлимитные', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Безлимитные'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Слайдер', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какой тип тарифов подходит для активных пользователей, которые каждый день потребляют интернет?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Слайдер'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Тарифы для юридических лиц обсуждаются:', 'ЮЛ — только через менеджера. Оператор не обсуждает коммерческие условия с юрлицами.',
       'single'::helpdesk.kb_question_selection_mode, 1630, TRUE,
       ARRAY['lineyki-tarifov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Оператором напрямую', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Оператором напрямую'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через менеджера (cm@wifitochka.ru)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через менеджера (cm@wifitochka.ru)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Автоматически в ЛК', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Тарифы для юридических лиц обсуждаются:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Автоматически в ЛК'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужно собрать при обращении потенциального абонента-физлица?', 'Для физлица: ФИО, телефон, адрес, наличие желающих среди соседей (важно для окупаемости установки).',
       'single'::helpdesk.kb_question_selection_mode, 1640, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только телефон', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только телефон'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'ФИО, телефон, адрес, есть ли желающие среди соседей', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'ФИО, телефон, адрес, есть ли желающие среди соседей'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только адрес', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении потенциального абонента-физлица?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только адрес'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?', 'Для ЮЛ: ФИО контактного лица, телефон, адрес, потенциальное количество абонентов.',
       'single'::helpdesk.kb_question_selection_mode, 1650, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Те же, что для физлица, плюс потенциальное количество абонентов', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Те же, что для физлица, плюс потенциальное количество абонентов'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только название организации', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только название организации'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только телефон', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Какие данные нужно собрать при обращении юрлица или вахтового посёлка?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только телефон'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'После сбора данных потенциального абонента оператор должен:', 'Создать заявку на новое подключение с указанием всех данных. Не обещать, что подключение состоится.',
       'single'::helpdesk.kb_question_selection_mode, 1660, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Пообещать подключение в ближайшее время', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Пообещать подключение в ближайшее время'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Создать заявку с указанием всех собранных данных', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Создать заявку с указанием всех собранных данных'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить на сайт компании', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'После сбора данных потенциального абонента оператор должен:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить на сайт компании'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?', 'Решение принимается на основе количества заявок от жителей. Чем больше желающих — тем выше вероятность.',
       'single'::helpdesk.kb_question_selection_mode, 1670, TRUE,
       ARRAY['novye-podklyucheniya']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'От количества желающих подключиться', TRUE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'От количества желающих подключиться'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'От суммы, которую готов заплатить абонент', FALSE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'От суммы, которую готов заплатить абонент'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Ни от чего, мы не подключаем новые НП', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если в населённом пункте нет нашего оборудования, от чего зависит решение о подключении?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Ни от чего, мы не подключаем новые НП'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Каков основной принцип подключения новых населённых пунктов?', 'Новые НП подключаются через местных партнёров-предпринимателей, которые устанавливают оборудование.',
       'single'::helpdesk.kb_question_selection_mode, 1680, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через прямой выезд наших инженеров', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через прямой выезд наших инженеров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через развитие партнёрской сети (местных предпринимателей)', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через развитие партнёрской сети (местных предпринимателей)'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Через заявки абонентов на сайте', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Каков основной принцип подключения новых населённых пунктов?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Через заявки абонентов на сайте'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?', 'Собрать данные и передать заявку. Объяснить, что решение принимается на основе количества желающих.',
       'single'::helpdesk.kb_question_selection_mode, 1690, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сказать, что подключение невозможно', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сказать, что подключение невозможно'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Собрать данные, создать заявку, объяснить про партнёрскую модель', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Собрать данные, создать заявку, объяснить про партнёрскую модель'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Отправить на сайт', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Если звонит человек и хочет подключиться, но в его НП нет покрытия — что делать?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Отправить на сайт'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'На основной сайт компании мы отправляем:', 'На сайт отправляем только потенциальных партнёров, не физлиц. Под физлиц разработан другой процесс.',
       'single'::helpdesk.kb_question_selection_mode, 1700, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'На основной сайт компании мы отправляем:'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Абонентов-физлиц для подключения', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Абонентов-физлиц для подключения'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Только потенциальных партнёров', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Только потенциальных партнёров'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Всех желающих', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'На основной сайт компании мы отправляем:'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Всех желающих'
  );

INSERT INTO helpdesk.kb_questions (
    quiz_id, question_text, explanation, selection_mode, sort_order, is_active, tags
)
SELECT q.id, 'Кем может быть партнёр для подключения нового населённого пункта?', 'Партнёр — это местный предприниматель, который устанавливает оборудование и может подключать односельчан.',
       'single'::helpdesk.kb_question_selection_mode, 1710, TRUE,
       ARRAY['razvitie-partnerskoy-seti-i-podklyuchenie-novyh-naselennyh-punktov']::text[]
FROM helpdesk.kb_quizzes q
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_questions qq
      WHERE qq.quiz_id = q.id AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Любым жителем', FALSE, 0
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Любым жителем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Местным предпринимателем', TRUE, 10
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Местным предпринимателем'
  );

INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qq.id, 'Сотрудником компании', FALSE, 20
FROM helpdesk.kb_questions qq
JOIN helpdesk.kb_quizzes q ON q.id = qq.quiz_id
JOIN helpdesk.kb_articles a ON a.id = q.article_id
WHERE a.slug = 'daily-warmup'
  AND qq.question_text = 'Кем может быть партнёр для подключения нового населённого пункта?'
  AND NOT EXISTS (
      SELECT 1 FROM helpdesk.kb_question_options o
      WHERE o.question_id = qq.id AND o.option_text = 'Сотрудником компании'
  );



-- Политика ежедневного теста (обновить quiz_id, если политика уже есть)

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



COMMIT;



-- Статистика после импорта:

-- SELECT a.slug, COUNT(qq.id) AS questions
-- FROM helpdesk.kb_articles a
-- JOIN helpdesk.kb_quizzes q ON q.article_id = a.id
-- LEFT JOIN helpdesk.kb_questions qq ON qq.quiz_id = q.id
-- GROUP BY a.slug ORDER BY a.slug;
