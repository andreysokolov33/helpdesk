BEGIN;

-- IP-адрес подключения абонента ≠ IP-адрес страницы авторизации
DELETE FROM helpdesk.kb_articles WHERE slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii';
INSERT INTO helpdesk.kb_articles (category_id, title, slug, subtitle, summary, content_html, sidebar_json, sort_order, is_published, pass_score_percent, quiz_required, published_at)
SELECT c.id, 'IP-адрес подключения абонента ≠ IP-адрес страницы авторизации', 'ip-podklyucheniya-vs-stranitsa-avtorizatsii', 'Как отличить один адрес от другого и откуда брать верный, чтобы продиктовать абоненту', 'Как отличить один адрес от другого и откуда брать верный, чтобы продиктовать абоненту Суть проблемы У абонента два разных IP — их легко перепутать Когда абонент подключается через HOTSPOT , в системе появляются два разных IP-адреса , и они относятся к совершенно разным вещам: IP подключения абонента',
'<div class="section-card" id="sec-intro">
    <div class="section-lbl">Суть проблемы</div>
    <h2>У абонента два разных IP — их легко перепутать</h2>
    <p>Когда абонент подключается через <span class="term-inline">HOTSPOT</span>, в системе появляются <strong>два разных IP-адреса</strong>, и они относятся к совершенно разным вещам:</p>
    <ul>
        <li><strong>IP подключения абонента</strong> — адрес, который получило его устройство прямо сейчас. Меняется от сессии к сессии. Это просто техническая метка, что абонент в сети — по этому адресу страница авторизации не откроется.</li>
        <li><strong>IP страницы авторизации</strong> — адрес, на котором абонент вводит логин и пароль, чтобы попасть в интернет. Он не меняется и хранится в карточке абонента.</li>
    </ul>
    <p>Это два адреса с разным смыслом и разным назначением — их не нужно путать между собой. Если продиктовать абоненту IP подключения вместо адреса страницы — он никогда не сможет открыть эту страницу, сколько бы ни пытался.</p>
    <div class="pl-info"><strong>Запомнить простыми словами:</strong> <span class="term-inline">IP подключения</span> — «где абонент сейчас в сети» (технический параметр, меняется каждый раз при новом подключении). <span class="term-inline bad">IP страницы авторизации</span> — «куда ему нужно зайти, чтобы включить интернет» (постоянный адрес, хранится в карточке абонента).</div>
</div>

<div class="section-card" id="sec-case">
    <div class="section-lbl">Пример</div>
    <h2>Как выглядит эта ошибка в переписке с абонентом</h2>
    <p>Ниже — пример переписки, показывающий типичную ошибку: оператор присылает абоненту не тот IP, и страница у абонента не открывается.</p>

    <div class="case-shot-wrap">
        <img src="/static/images/kb/hotspot-ip-chat-example.webp" alt="Пример переписки: оператор сообщает IP-адрес, абонент отвечает, что страница не загружается" loading="lazy" />
        <div class="case-fig">Пример переписки: абоненту продиктован не тот адрес, поэтому страница у него не открывается.</div>
    </div>

    <div class="rule">
        <div class="rule-title">Главное правило</div>
        IP-адрес подключения абонента к сети и IP-адрес страницы авторизации (hotspot) — это <strong>разные адреса</strong>. Абоненту нужно диктовать IP страницы авторизации из карточки абонента, а не IP из журнала сессий.
    </div>
</div>

<div class="section-card" id="sec-where">
    <div class="section-lbl">Где смотреть</div>
    <h2>Где в системе найти каждый из двух адресов</h2>
    <p>У каждого IP — своё место в системе. Если перепутать место поиска, легко продиктовать абоненту не тот адрес.</p>

    <h3>1. IP подключения — журнал сессий абонента</h3>
    <p>Открываем журнал сессий абонента. В таблице есть колонка <strong>«IP»</strong> — это и есть IP подключения. Он меняется почти в каждой новой сессии. <strong>Этот адрес абоненту диктовать не нужно</strong> — это не адрес страницы.</p>
    <div class="case-shot-wrap">
        <img src="/static/images/kb/hotspot-ip-session-log.webp" alt="Журнал сессий абонента: колонка IP показывает технический адрес подключения" loading="lazy" />
        <div class="case-fig">Журнал сессий: колонка «IP» — это IP подключения абонента, не адрес страницы авторизации.</div>
    </div>

    <h3>2. IP страницы авторизации — карточка абонента</h3>
    <p>Открываем карточку абонента. В ней есть отдельное поле <strong>«Страница авторизации»</strong> — вот это и есть верный адрес, который нужно продиктовать абоненту. Этот адрес не меняется от сессии к сессии.</p>
    <div class="case-shot-wrap">
        <img src="/static/images/kb/hotspot-ip-user-card.webp" alt="Карточка абонента: поле «Страница авторизации» содержит верный IP-адрес" loading="lazy" />
        <div class="case-fig">Карточка абонента: поле «Страница авторизации» — именно этот IP нужно диктовать абоненту.</div>
    </div>

    <div class="rule">
        <div class="rule-title">Короткое правило для оператора</div>
        Диктуем абоненту IP только из поля <strong>«Страница авторизации»</strong> в карточке абонента. Колонку «IP» в журнале сессий для этого не используем.
    </div>
</div>

<div class="section-card" id="sec-diff">
    <div class="section-lbl">Запомнить просто</div>
    <h2>Два адреса рядом — какой за что отвечает</h2>
    <div class="scheme">
        <div class="card-ip bad">
            <div class="k">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                IP подключения абонента
            </div>
            <div class="card-ip__val">Журнал сессий, колонка «IP»</div>
            <div class="d">Меняется почти каждый раз, когда абонент заново подключается к сети. Показывает только, что абонент «в сети» сейчас — технический параметр его устройства. Диктовать абоненту не нужно — страница по этому адресу не откроется.</div>
        </div>
        <div class="scheme-eq">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="9" x2="19" y2="9"/><line x1="5" y1="15" x2="19" y2="15"/><line x1="5" y1="4" x2="19" y2="20"/></svg>
        </div>
        <div class="card-ip ok">
            <div class="k">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                IP страницы авторизации
            </div>
            <div class="card-ip__val">Карточка абонента, поле «Страница авторизации»</div>
            <div class="d">Не меняется — постоянный адрес. Именно этот адрес абонент должен открыть в браузере, чтобы ввести логин и пароль и получить доступ в интернет. Его и нужно диктовать.</div>
        </div>
    </div>
    <p>Самый простой способ не ошибиться: журнал сессий — источник IP подключения, его абоненту диктовать не нужно; карточка абонента, поле «Страница авторизации» — единственное место, откуда берётся адрес для диктовки.</p>
</div>',
'{"quick_access": [{"label": "Суть проблемы", "anchor": "sec-intro"}, {"label": "Пример ошибки", "anchor": "sec-case"}, {"label": "Где смотреть каждый IP", "anchor": "sec-where"}, {"label": "Какой за что отвечает", "anchor": "sec-diff"}]}'::jsonb, 270, TRUE, 100, TRUE, NOW()
FROM helpdesk.kb_categories c WHERE c.slug = 'podklyuchenie-i-internet';
INSERT INTO helpdesk.kb_quizzes (article_id, title, passing_score_percent)
SELECT a.id, 'Проверка знаний темы: IP-адрес подключения абонента ≠ IP-адрес страницы авторизации', 100 FROM helpdesk.kb_articles a WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii';
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Абонент сообщает, что страница авторизации не загружается по адресу, который ему продиктовал оператор. В чём может быть причина?', 'Самая частая причина такой жалобы — оператор взял адрес из колонки «IP» журнала сессий. Это адрес устройства абонента, а не адрес страницы входа, поэтому страница по нему никогда не откроется.', 'single', 10, ARRAY['ip-podklyucheniya-vs-stranitsa-avtorizatsii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Оператор продиктовал IP-адрес подключения абонента из журнала сессий, а не адрес страницы авторизации из карточки абонента', TRUE, 0),
  ('У абонента сломался телефон', FALSE, 10),
  ('Это нормально, страница должна открываться только через сутки', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Где находится IP-адрес подключения абонента, который меняется от сессии к сессии?', 'IP-адрес подключения назначается устройству автоматически при каждом новом подключении и отображается в журнале сессий в колонке «IP» — это технический параметр, не адрес веб-страницы.', 'single', 20, ARRAY['ip-podklyucheniya-vs-stranitsa-avtorizatsii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('В журнале сессий абонента, в колонке «IP»', TRUE, 0),
  ('В карточке абонента, в поле «Страница авторизации»', FALSE, 10),
  ('На коробке от роутера', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Где нужно искать правильный адрес страницы авторизации, который можно продиктовать абоненту?', 'Адрес страницы авторизации хранится в карточке абонента, в отдельном поле «Страница авторизации», и не меняется от сессии к сессии — именно его нужно диктовать.', 'single', 30, ARRAY['ip-podklyucheniya-vs-stranitsa-avtorizatsii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('В журнале сессий абонента вместе с IP подключения', FALSE, 0),
  ('В карточке абонента, в поле «Страница авторизации»', TRUE, 10),
  ('В истории платежей абонента', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Почему IP подключения и IP страницы авторизации легко перепутать?', 'IP подключения и IP страницы авторизации внешне выглядят как обычные цифровые адреса, поэтому оператору легко случайно продиктовать не тот, если не проверить источник: журнал сессий даёт IP подключения (его диктовать не нужно), а карточка абонента — адрес страницы авторизации (его и нужно диктовать).', 'single', 40, ARRAY['ip-podklyucheniya-vs-stranitsa-avtorizatsii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Потому что они оба записываются зелёным цветом в системе', FALSE, 0),
  ('Потому что оба адреса — это просто набор цифр через точку, и при беглом взгляде легко принять один за другой, не проверив, откуда он взят', TRUE, 10),
  ('Их невозможно перепутать, это разные форматы записи', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Абонент повторно написал, что страница так и не открывается, уже после продиктованного адреса. Что нужно сделать оператору первым делом?', 'Повторная жалоба после уже продиктованного адреса — явный сигнал проверить источник этого адреса: если он был взят из журнала сессий, страница по нему не откроется никогда, и нужно продиктовать верный адрес из карточки абонента.', 'single', 50, ARRAY['ip-podklyucheniya-vs-stranitsa-avtorizatsii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'ip-podklyucheniya-vs-stranitsa-avtorizatsii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Попросить абонента перезагрузить телефон пять раз', FALSE, 0),
  ('Проверить, не был ли продиктованный адрес на самом деле IP-адресом подключения из журнала сессий, а не адресом из карточки абонента', TRUE, 10),
  ('Сразу оформить заявку инженерам без проверки', FALSE, 20)
) AS v(t, c, o);

-- Почему нельзя долго держать абонента на линии с паузами
DELETE FROM helpdesk.kb_articles WHERE slug = 'dolgoe-uderzhanie-na-linii';
INSERT INTO helpdesk.kb_articles (category_id, title, slug, subtitle, summary, content_html, sidebar_json, sort_order, is_published, pass_score_percent, quiz_required, published_at)
SELECT c.id, 'Почему нельзя долго держать абонента на линии с паузами', 'dolgoe-uderzhanie-na-linii', 'Что происходит с абонентом в долгой тишине и как возвращаться к диалогу, чтобы этого не было', 'Что происходит с абонентом в долгой тишине и как возвращаться к диалогу, чтобы этого не было Суть проблемы Тишина на линии работает против нас, даже если решение верное Пока оператор молча ищет информацию в системе, абонент слышит только тишину (или музыку) и не понимает: его слушают, про него забыл',
'<div class="section-card" id="sec-intro">
    <div class="section-lbl">Суть проблемы</div>
    <h2>Тишина на линии работает против нас, даже если решение верное</h2>
    <p>Пока оператор молча ищет информацию в системе, абонент слышит только тишину (или музыку) и не понимает: его слушают, про него забыли, связь пропала или звонок уже оборвался. Абонент не видит экран оператора — для него существует только одно: <strong>с ним говорят или его бросили</strong>.</p>
    <div class="pl-info"><strong>Важно понимать:</strong> проблема не в том, что решение занимает время — абонент готов подождать. Проблема в том, что он не знает, <span class="term-inline bad">сколько именно</span> ждать и <span class="term-inline bad">происходит ли что-то вообще</span>. Именно эта неизвестность создаёт тревогу и раздражение.</div>
</div>

<div class="section-card" id="sec-why">
    <div class="section-lbl">Почему это происходит</div>
    <h2>Что чувствует абонент в долгой тишине</h2>
    <div class="reason-grid">
        <div class="reason-card">
            <div class="rc-head"><div class="reason-icon">1</div><div class="rc-title">Неизвестность хуже ожидания</div></div>
            <p class="rc-text">Абонент готов подождать 2 минуты, если знает, что это займёт 2 минуты. Но без ориентира по времени каждая секунда тишины воспринимается как потенциально бесконечная.</p>
        </div>
        <div class="reason-card">
            <div class="rc-head"><div class="reason-icon">2</div><div class="rc-title">Тишина похожа на обрыв связи</div></div>
            <p class="rc-text">Абонент не может отличить «оператор работает» от «связь пропала» или «меня забыли» — и после 30-40 секунд тишины начинает сомневаться, что его вообще слушают.</p>
        </div>
        <div class="reason-card">
            <div class="rc-head"><div class="reason-icon">3</div><div class="rc-title">Раздражение уходит не по адресу</div></div>
            <p class="rc-text">Абонент не злится на паузу напрямую — он злится на тариф, качество связи, компанию в целом. Сама пауза становится триггером для претензий, которых не было в начале разговора.</p>
        </div>
        <div class="reason-card">
            <div class="rc-head"><div class="reason-icon">4</div><div class="rc-title">Доверие к результату снижается</div></div>
            <p class="rc-text">Даже если решение в итоге правильное, абонент запоминает не решение, а ощущение «меня бросили» — и это влияет на оценку всего разговора.</p>
        </div>
    </div>
</div>

<div class="section-card" id="sec-howto">
    <div class="section-lbl">Как делать правильно</div>
    <h2>Возвращаться к диалогу каждые 45-60 секунд</h2>
    <p>Правило простое: если решение вопроса требует паузы дольше минуты — <strong>не уходите в тишину надолго</strong>. Возвращайтесь к абоненту каждые 45-60 секунд, даже если задача ещё не решена.</p>
    <div class="check-card-list">
        <div class="check-card-item">
            <div class="check-card-icon">1</div>
            <div class="check-card-text"><strong>Сообщить, что уже происходит</strong>«Я сейчас проверяю данные по вашему тарифу» — абонент понимает, что процесс идёт, а не завис.</div>
        </div>
        <div class="check-card-item">
            <div class="check-card-icon">2</div>
            <div class="check-card-text"><strong>Обозначить этап</strong>«Нашёл причину, сейчас формирую заявку» — абонент видит, что дело движется вперёд, а не стоит на месте.</div>
        </div>
        <div class="check-card-item">
            <div class="check-card-icon">3</div>
            <div class="check-card-text"><strong>Задать уточняющий вопрос, если он нужен</strong>Вместо тишины можно использовать это время для уточнения деталей — и абонент занят диалогом, а не ожиданием.</div>
        </div>
        <div class="check-card-item">
            <div class="check-card-icon">4</div>
            <div class="check-card-text"><strong>Назвать ориентир по времени</strong>«Потребуется ещё пара минут» — это снимает самое неприятное: неизвестность, сколько ждать.</div>
        </div>
        <div class="check-card-item">
            <div class="check-card-icon">5</div>
            <div class="check-card-text"><strong>Поблагодарить за ожидание при возвращении</strong>Простое «спасибо, что подождали» показывает, что оператор помнит про абонента и ценит его время.</div>
        </div>
    </div>
    <div class="pl-info"><strong>Ориентиры по времени:</strong><br>● Возвращайтесь к диалогу <strong>каждые 45-60 секунд</strong>: сообщите этап, задайте вопрос или назовите срок.<br>● Зона риска — <strong>5-7 минут</strong> суммарного удержания на линии: у абонента появляется ощущение покинутости.</div>
    <div class="rule">
        <div class="rule-title">Главное правило</div>
        Если пауза неизбежна — назовите абоненту примерный срок («ещё пара минут») и возвращайтесь к диалогу не реже чем раз в 45-60 секунд. Тогда у абонента нет ощущения, что он ждёт неизвестно сколько, — а значит нет и раздражения, которое возникает не из-за самой проблемы, а из-за тишины на линии.
    </div>
</div>',
'{"quick_access": [{"label": "Суть проблемы", "anchor": "sec-intro"}, {"label": "Почему это происходит", "anchor": "sec-why"}, {"label": "Как делать правильно", "anchor": "sec-howto"}]}'::jsonb, 280, TRUE, 100, TRUE, NOW()
FROM helpdesk.kb_categories c WHERE c.slug = 'rabota-s-abonentami';
INSERT INTO helpdesk.kb_quizzes (article_id, title, passing_score_percent)
SELECT a.id, 'Проверка знаний темы: Почему нельзя долго держать абонента на линии с паузами', 100 FROM helpdesk.kb_articles a WHERE a.slug = 'dolgoe-uderzhanie-na-linii';
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Почему тишина на линии воспринимается абонентом хуже, чем сама задержка в решении вопроса?', 'Абонент не видит, что делает оператор. Тишина не говорит ему, идёт ли работа, пропала ли связь или про него забыли — и именно эта неизвестность создаёт тревогу, а не сама длительность ожидания.', 'single', 10, ARRAY['dolgoe-uderzhanie-na-linii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'dolgoe-uderzhanie-na-linii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Потому что абонент не готов ждать вообще никогда', FALSE, 0),
  ('Потому что без информации о происходящем абонент не может отличить работу оператора от обрыва связи или забытого звонка', TRUE, 10),
  ('Потому что музыка на удержании звучит слишком громко', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Как часто нужно возвращаться к диалогу с абонентом во время паузы в разговоре?', 'Правило — возвращаться к диалогу каждые 45-60 секунд: сообщать этап, задавать вопрос или называть примерный срок. Это не даёт тишине растянуться настолько, чтобы абонент почувствовал себя забытым.', 'single', 20, ARRAY['dolgoe-uderzhanie-na-linii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'dolgoe-uderzhanie-na-linii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Раз в 10-15 минут, чтобы не мешать работе', FALSE, 0),
  ('Каждые 45-60 секунд', TRUE, 10),
  ('Только один раз — в самом начале паузы', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Почему тишина на линии особенно сильно подрывает доверие абонента, даже если проблема в итоге решена правильно?', 'Даже правильное решение не спасает впечатление от разговора, если абонент долго молчал в тишине. Запоминается в первую очередь ощущение «со мной перестали разговаривать», а не итоговый результат.', 'single', 30, ARRAY['dolgoe-uderzhanie-na-linii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'dolgoe-uderzhanie-na-linii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Потому что абонент всегда забывает, зачем звонил', FALSE, 0),
  ('Потому что абонент запоминает не решение, а ощущение, что его бросили на время паузы — и это влияет на оценку всего разговора', TRUE, 10),
  ('Потому что решение проблемы должно занимать не более 10 секунд', FALSE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Какая фраза лучше всего снимает у абонента ощущение «неизвестно, сколько ждать»?', 'Называние примерного срока («ещё пара минут») даёт абоненту ориентир по времени — он понимает, что ждать осталось немного, и неизвестность, самая неприятная часть ожидания, снимается.', 'single', 40, ARRAY['dolgoe-uderzhanie-na-linii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'dolgoe-uderzhanie-na-linii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Полное молчание до завершения задачи', FALSE, 0),
  ('«Оставайтесь на линии» без дальнейших слов', FALSE, 10),
  ('«Решение вопроса потребует ещё пару минут»', TRUE, 20)
) AS v(t, c, o);
WITH qn AS (INSERT INTO helpdesk.kb_questions (quiz_id, question_text, explanation, selection_mode, sort_order, tags)
  SELECT z.id, 'Абонент на паузе в разговоре. Что из перечисленного — правильное поведение оператора?', 'Правило — возвращаться к диалогу не реже чем раз в 45-60 секунд, сообщая этап работы, задавая уточняющий вопрос или называя примерный срок ожидания. Это не даёт абоненту почувствовать себя забытым.', 'single', 50, ARRAY['dolgoe-uderzhanie-na-linii']
  FROM helpdesk.kb_quizzes z JOIN helpdesk.kb_articles a ON a.id = z.article_id WHERE a.slug = 'dolgoe-uderzhanie-na-linii' RETURNING id)
INSERT INTO helpdesk.kb_question_options (question_id, option_text, is_correct, sort_order)
SELECT qn.id, v.t, v.c, v.o FROM qn, (VALUES
  ('Полностью промолчать до момента, пока вопрос не решится', FALSE, 0),
  ('Каждые 45-60 секунд возвращаться к диалогу: сообщать этап, задавать уточняющий вопрос или называть примерный срок', TRUE, 10),
  ('Сказать абоненту один раз «подождите» и больше не возвращаться к разговору', FALSE, 20)
) AS v(t, c, o);

COMMIT;
