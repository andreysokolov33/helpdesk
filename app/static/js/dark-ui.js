/* ============================================
   СИСТЕМА АЛЕРТОВ (Toast уведомления)
   ============================================
   
   Использование:
   
   1. Простой вызов:
      DarkToast.success('Операция выполнена успешно');
      DarkToast.error('Произошла ошибка');
      DarkToast.warn('Внимание! Проверьте данные');
   
   2. С заголовком:
      DarkToast.success('Данные сохранены', 'Успешно');
      DarkToast.error('Не удалось подключиться', 'Ошибка сети');
   
   3. Расширенный вызов:
      DarkToast.show({
        type: 'success',  // 'success', 'error', 'warn'
        title: 'Заголовок',
        msg: 'Сообщение',
        timeout: 5000  // время показа в мс (0 = не закрывать автоматически)
      });
   
   4. Программное закрытие:
      const toast = DarkToast.success('Сообщение');
      toast.close(); // закрыть вручную
*/

const DarkToast = (() => {
    const container = document.getElementById('darkToastContainer');
    if (!container) {
        console.warn('DarkToast: контейнер не найден');
        return { show: () => { }, success: () => { }, error: () => { }, warn: () => { } };
    }

    function make(type, title, msg, timeout = 3500) {
        const el = document.createElement('div');
        el.className = `dark-toast dark-toast--${type}`;
        el.innerHTML = `
      <div aria-hidden="true" style="margin-top:2px">
        ${type === 'success'
                ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
                : type === 'warn'
                    ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 8v5m0 3h.01M3 19h18L12 4 3 19z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
                    : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'}
      </div>
      <div>
        <div class="dark-toast__title">${title || ''}</div>
        ${msg ? `<div class="dark-toast__msg">${msg}</div>` : ''}
      </div>
      <button class="dark-toast__close" aria-label="Закрыть">✕</button>
    `;
        const close = () => {
            el.style.animation = 'toast-out .18s ease forwards';
            setTimeout(() => el.remove(), 180);
        };
        el.querySelector('.dark-toast__close').addEventListener('click', close);
        container.appendChild(el);
        if (timeout > 0) setTimeout(close, timeout);
        return { close, el };
    }
    return {
        show: (opts) => {
            const { type = 'success', title = '', msg = '', timeout = 3500 } = opts || {};
            return make(type, title, msg, timeout);
        },
        success: (msg, title = 'Готово') => make('success', title, msg),
        info: (msg, title = 'Готово') => make('success', title, msg),
        error: (msg, title = 'Ошибка') => make('error', title, msg),
        warn: (msg, title = 'Внимание') => make('warn', title, msg),
    };
})();

/* ============================================
   МОДАЛЬНЫЕ ОКНА ПОДТВЕРЖДЕНИЯ
   ============================================
   
   Использование:
   
   1. Простое подтверждение:
      const confirmed = await DarkConfirm.open({
        title: 'Удалить запись?',
        message: 'Это действие нельзя отменить'
      });
      if (confirmed) {
        // Пользователь нажал ОК
      }
   
   2. С опасной кнопкой:
      const confirmed = await DarkConfirm.open({
        title: 'Удалить навсегда?',
        message: 'Все данные будут потеряны',
        danger: true  // кнопка ОК будет красной
      });
   
   3. С кастомными текстами кнопок:
      const confirmed = await DarkConfirm.open({
        title: 'Сохранить изменения?',
        message: 'Несохраненные изменения будут потеряны',
        okText: 'Сохранить',
        cancelText: 'Отменить'
      });
*/

const DarkConfirm = (() => {
    const overlay = document.getElementById('darkConfirmOverlay');
    if (!overlay) {
        console.warn('DarkConfirm: контейнер не найден');
        return { open: () => Promise.resolve(false), close: () => { }, consumeRedirectToNews: () => false };
    }

    const titleEl = document.getElementById('darkConfirmTitle');
    const msgEl = document.getElementById('darkConfirmMessage');
    const extraEl = document.getElementById('darkConfirmExtra');
    const btnOk = document.getElementById('darkConfirmOk');
    const btnCancel = document.getElementById('darkConfirmCancel');

    let resolver = null;
    /** После «ОК»: перенаправить на создание новости (читается через consumeRedirectToNews). */
    let pendingRedirectToNews = false;

    function open({
        title = 'Подтвердите действие',
        message = 'Вы уверены?',
        okText = 'ОК',
        cancelText = 'Отмена',
        danger = false,
        extraHtml = null,
    } = {}) {
        pendingRedirectToNews = false;
        titleEl.textContent = title;
        msgEl.textContent = message;
        btnOk.textContent = okText;
        btnCancel.textContent = cancelText;

        if (extraEl) {
            if (extraHtml) {
                extraEl.innerHTML = extraHtml;
                extraEl.hidden = false;
            } else {
                extraEl.innerHTML = '';
                extraEl.hidden = true;
            }
        }

        btnOk.classList.toggle('dark-btn--danger', !!danger);

        overlay.classList.add('is-open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';

        return new Promise((resolve) => {
            resolver = resolve;
        });
    }

    function close(result) {
        if (!result) pendingRedirectToNews = false;
        overlay.classList.remove('is-open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        if (extraEl) {
            extraEl.innerHTML = '';
            extraEl.hidden = true;
        }
        if (resolver) {
            resolver(result);
            resolver = null;
        }
    }

    function consumeRedirectToNews() {
        const v = pendingRedirectToNews;
        pendingRedirectToNews = false;
        return v;
    }

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close(false);
    });
    btnCancel.addEventListener('click', () => close(false));
    btnOk.addEventListener('click', () => {
        const cb = document.getElementById('darkConfirmRedirectNews');
        pendingRedirectToNews = !!(cb && cb.checked);
        close(true);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('is-open')) close(false);
    });

    const api = { open, close, consumeRedirectToNews };
    if (typeof window !== 'undefined') window.DarkConfirm = api;
    return api;
})();

/* ============================================
   ДАТАПИКЕР (Выбор даты)
   ============================================
   
   Использование:
   
   1. Инициализация на input элементе:
      <input type="text" id="myDateInput" class="datepicker-input">
      <script>
        DatePicker.init('#myDateInput', {
          format: 'dd.mm.yyyy',  // формат отображения
          minDate: new Date(),   // минимальная дата
          maxDate: null,         // максимальная дата (null = без ограничений)
          locale: 'ru'           // локаль (ru/en)
        });
      </script>
   
   2. Получение выбранной даты:
      const date = DatePicker.getValue('#myDateInput');
      // возвращает Date объект или null
   
   3. Установка даты программно:
      DatePicker.setValue('#myDateInput', new Date('2024-01-15'));
   
   4. Закрытие календаря:
      DatePicker.close('#myDateInput');
*/

const DatePicker = (() => {
    const instances = new Map();
    const monthsRu = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    const monthsEn = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const weekdaysRu = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    const weekdaysEn = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    function formatDate(date, format) {
        if (!date) return '';
        const d = date.getDate().toString().padStart(2, '0');
        const m = (date.getMonth() + 1).toString().padStart(2, '0');
        const y = date.getFullYear();
        return format.replace('dd', d).replace('mm', m).replace('yyyy', y);
    }

    function parseDate(str, format) {
        if (!str) return null;
        const parts = str.split(/[.\-\/]/);
        if (parts.length !== 3) return null;
        const formatParts = format.split(/[.\-\/]/);
        let day, month, year;
        formatParts.forEach((part, i) => {
            if (part === 'dd') day = parseInt(parts[i], 10);
            else if (part === 'mm') month = parseInt(parts[i], 10) - 1;
            else if (part === 'yyyy') year = parseInt(parts[i], 10);
        });
        if (day === undefined || month === undefined || year === undefined) return null;
        return new Date(year, month, day);
    }

    function dateOnly(d) {
        if (!d) return null;
        return new Date(d.getFullYear(), d.getMonth(), d.getDate());
    }

    function createCalendar(input, options) {
        const wrapper = document.createElement('div');
        wrapper.className = 'datepicker-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        input.classList.add('datepicker-input');

        const calendar = document.createElement('div');
        calendar.className = 'datepicker-calendar';
        calendar.style.display = 'none';
        wrapper.appendChild(calendar);

        let selectedDate = parseDate(input.value, options.format);
        let currentDate = selectedDate ? new Date(selectedDate) : new Date();
        let viewMode = 'days';

        const locale = options.locale || 'ru';
        const months = locale === 'ru' ? monthsRu : monthsEn;
        const weekdays = locale === 'ru' ? weekdaysRu : weekdaysEn;

        function resolveMinMax() {
            const minD = typeof options.minDate === 'function' ? options.minDate() : options.minDate;
            let maxD = typeof options.maxDate === 'function' ? options.maxDate() : options.maxDate;
            if (options.noFuture && (!maxD || dateOnly(maxD) > dateOnly(new Date()))) {
                const today = new Date();
                today.setHours(23, 59, 59, 999);
                maxD = maxD ? (dateOnly(maxD) < dateOnly(today) ? maxD : today) : today;
            }
            return { minD: minD ? dateOnly(minD) : null, maxD: maxD ? dateOnly(maxD) : null };
        }

        function renderCalendar() {
            const { minD, maxD } = resolveMinMax();
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();

            if (viewMode === 'months') {
                calendar.innerHTML = `
                    <div class="datepicker-header datepicker-header--sub">
                        <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="prev-year" aria-label="Предыдущий год">‹</button>
                        <div class="datepicker-month-year"><span class="datepicker-header-year">${year}</span></div>
                        <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="next-year" aria-label="Следующий год">›</button>
                    </div>
                    <div class="datepicker-header-divider" aria-hidden="true"></div>
                    <div class="datepicker-months-list"></div>
                `;
                const grid = calendar.querySelector('.datepicker-months-list');
                for (let m = 0; m < 12; m++) {
                    const btn = document.createElement('button');
                    btn.className = 'datepicker-month-btn' + (m === month ? ' selected' : '');
                    btn.textContent = months[m];
                    const firstDay = new Date(year, m, 1);
                    const lastDay = new Date(year, m + 1, 0);
                    const disabled = (minD && lastDay < minD) || (maxD && firstDay > maxD);
                    if (disabled) btn.classList.add('disabled');
                    else btn.addEventListener('click', () => {
                        currentDate.setMonth(m);
                        viewMode = 'days';
                        renderCalendar();
                    });
                    grid.appendChild(btn);
                }
                const maxY = options.maxYear != null ? options.maxYear : 9999;
                const minY = options.minYear != null ? options.minYear : 1900;
                calendar.querySelector('[data-action="prev-year"]').addEventListener('click', () => {
                    currentDate.setFullYear(Math.max(minY, currentDate.getFullYear() - 1));
                    renderCalendar();
                });
                calendar.querySelector('[data-action="next-year"]').addEventListener('click', () => {
                    currentDate.setFullYear(Math.min(maxY, currentDate.getFullYear() + 1));
                    renderCalendar();
                });
                calendar.querySelector('.datepicker-header-year').addEventListener('click', () => {
                    viewMode = 'years';
                    renderCalendar();
                });
                return;
            }

            if (viewMode === 'years') {
                const maxY = options.maxYear != null ? options.maxYear : new Date().getFullYear() + 10;
                const minY = options.minYear != null ? options.minYear : new Date().getFullYear() - 50;
                const yearStart = Math.max(minY, Math.floor(year / 10) * 10);
                calendar.innerHTML = `
                    <div class="datepicker-header datepicker-header--sub">
                        <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="prev-decade" aria-label="Предыдущее десятилетие">‹</button>
                        <div class="datepicker-month-year datepicker-month-year--range">${yearStart}–${Math.min(yearStart + 9, maxY)}</div>
                        <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="next-decade" aria-label="Следующее десятилетие">›</button>
                    </div>
                    <div class="datepicker-header-divider" aria-hidden="true"></div>
                    <div class="datepicker-years-list"></div>
                `;
                const grid = calendar.querySelector('.datepicker-years-list');
                for (let y = yearStart; y <= maxY && y < yearStart + 12; y++) {
                    const btn = document.createElement('button');
                    btn.className = 'datepicker-year-btn' + (y === year ? ' selected' : '');
                    btn.textContent = y;
                    const disabled = (minD && y < minD.getFullYear()) || (maxD && y > maxD.getFullYear());
                    if (disabled) btn.classList.add('disabled');
                    else btn.addEventListener('click', () => {
                        currentDate.setFullYear(y);
                        viewMode = 'days';
                        renderCalendar();
                    });
                    grid.appendChild(btn);
                }
                calendar.querySelector('[data-action="prev-decade"]').addEventListener('click', () => {
                    const next = Math.max(minY, currentDate.getFullYear() - 10);
                    currentDate.setFullYear(next);
                    renderCalendar();
                });
                calendar.querySelector('[data-action="next-decade"]').addEventListener('click', () => {
                    const next = Math.min(maxY, currentDate.getFullYear() + 10);
                    currentDate.setFullYear(next);
                    renderCalendar();
                });
                return;
            }

            viewMode = 'days';
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startDate = new Date(firstDay);
            startDate.setDate(startDate.getDate() - (firstDay.getDay() || 7) + 1);

            calendar.innerHTML = `
                <div class="datepicker-header datepicker-header--days">
                    <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="prev" aria-label="Предыдущий месяц">‹</button>
                    <div class="datepicker-header-selects">
                        <button type="button" class="datepicker-header-pill datepicker-header-month">${months[month]}</button>
                        <button type="button" class="datepicker-header-pill datepicker-header-year">${year}</button>
                    </div>
                    <button type="button" class="datepicker-nav-btn datepicker-nav-btn--ghost" data-action="next" aria-label="Следующий месяц">›</button>
                </div>
                <div class="datepicker-header-divider" aria-hidden="true"></div>
                <div class="datepicker-weekdays">
                    ${weekdays.map(wd => `<div class="datepicker-weekday">${wd}</div>`).join('')}
                </div>
                <div class="datepicker-days"></div>
            `;

            const daysContainer = calendar.querySelector('.datepicker-days');
            const date = new Date(startDate);

            for (let i = 0; i < 42; i++) {
                const dayDate = new Date(date);
                const dayBtn = document.createElement('button');
                dayBtn.className = 'datepicker-day';
                dayBtn.textContent = dayDate.getDate();

                if (dayDate.getMonth() !== month) {
                    dayBtn.classList.add('other-month');
                }

                const dateStr = dayDate.toDateString();
                const todayStr = new Date().toDateString();
                if (dateStr === todayStr) {
                    dayBtn.classList.add('today');
                }

                if (selectedDate && dateStr === selectedDate.toDateString()) {
                    dayBtn.classList.add('selected');
                }

                const dayOnly = dateOnly(dayDate);
                const disabled = (minD && dayOnly < minD) || (maxD && dayOnly > maxD);
                if (disabled) {
                    dayBtn.classList.add('disabled');
                } else {
                    dayBtn.addEventListener('click', () => {
                        selectedDate = new Date(dayDate);
                        input.value = formatDate(selectedDate, options.format);
                        calendar.style.display = 'none';
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        if (options.onSelect) options.onSelect(selectedDate);
                        renderCalendar();
                    });
                }

                daysContainer.appendChild(dayBtn);
                date.setDate(date.getDate() + 1);
            }

            const maxY = options.maxYear != null ? options.maxYear : 9999;
            const minY = options.minYear != null ? options.minYear : 1900;
            calendar.querySelector('[data-action="prev"]').addEventListener('click', () => {
                if (currentDate.getFullYear() === minY && currentDate.getMonth() === 0) return;
                currentDate.setMonth(currentDate.getMonth() - 1);
                renderCalendar();
            });
            calendar.querySelector('[data-action="next"]').addEventListener('click', () => {
                if (currentDate.getFullYear() === maxY && currentDate.getMonth() === 11) return;
                currentDate.setMonth(currentDate.getMonth() + 1);
                renderCalendar();
            });
            calendar.querySelector('.datepicker-header-month').addEventListener('click', () => {
                viewMode = 'months';
                renderCalendar();
            });
            calendar.querySelector('.datepicker-header-year').addEventListener('click', () => {
                viewMode = 'years';
                renderCalendar();
            });
        }

        input.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = calendar.style.display !== 'none';
            closeAllCalendars();
            if (!isVisible) {
                viewMode = 'days';
                renderCalendar();
                calendar.style.visibility = 'hidden';
                calendar.style.display = 'block';
                calendar.style.left = '0';
                calendar.style.right = 'auto';
                calendar.style.top = '100%';
                calendar.style.bottom = 'auto';
                calendar.style.marginTop = '4px';
                calendar.style.maxHeight = '';
                calendar.style.overflowY = '';

                requestAnimationFrame(() => {
                    const pad = 12;
                    const inputRect = input.getBoundingClientRect();
                    const calendarHeight = calendar.offsetHeight;
                    const spaceBelow = window.innerHeight - inputRect.bottom - pad;
                    const spaceAbove = inputRect.top - pad;

                    // Предпочитаем открытие вниз, чтобы избежать "прыжка" на мобилке.
                    // Вверх открываем только если снизу явно не хватает места, а сверху достаточно.
                    const shouldOpenUp = spaceBelow < calendarHeight && spaceAbove > spaceBelow;
                    if (shouldOpenUp) {
                        calendar.style.top = 'auto';
                        calendar.style.bottom = '100%';
                        calendar.style.marginTop = '';
                    } else {
                        calendar.style.top = '100%';
                        calendar.style.bottom = 'auto';
                        calendar.style.marginTop = '4px';
                    }

                    let r = calendar.getBoundingClientRect();
                    if (r.left < pad) {
                        const curLeft = parseFloat(calendar.style.left) || 0;
                        calendar.style.left = (curLeft + (pad - r.left)) + 'px';
                        r = calendar.getBoundingClientRect();
                    }
                    if (r.right > window.innerWidth - pad) {
                        const curLeft = parseFloat(calendar.style.left) || 0;
                        calendar.style.left = (curLeft - (r.right - (window.innerWidth - pad))) + 'px';
                        r = calendar.getBoundingClientRect();
                    }

                    if (r.bottom > window.innerHeight - pad) {
                        calendar.style.maxHeight = Math.max(180, window.innerHeight - r.top - pad) + 'px';
                        calendar.style.overflowY = 'auto';
                    }

                    calendar.style.visibility = 'visible';
                });
            }
        });

        input.addEventListener('blur', (e) => {
            const value = parseDate(input.value, options.format);
            if (value) {
                selectedDate = value;
                input.value = formatDate(value, options.format);
            }
        });

        instances.set(input, {
            calendar,
            format: options.format,
            selectedDate: () => selectedDate,
            setDate: (d) => {
                selectedDate = d;
                input.value = formatDate(d, options.format);
                renderCalendar();
            },
            renderCalendar
        });
        renderCalendar();
    }

    function closeAllCalendars() {
        instances.forEach(({ calendar }) => {
            calendar.style.display = 'none';
        });
    }

    document.addEventListener('click', (e) => {
        if (document.contains(e.target) && !e.target.closest('.datepicker-wrapper') && !e.target.closest('.datepicker-calendar')) {
            closeAllCalendars();
        }
    }, true);

    return {
        init: (selector, options = {}) => {
            const input = typeof selector === 'string' ? document.querySelector(selector) : selector;
            if (!input) {
                console.warn('DatePicker: элемент не найден', selector);
                return;
            }
            const opts = {
                format: options.format || 'dd.mm.yyyy',
                minDate: options.minDate || null,
                maxDate: options.maxDate || null,
                minYear: options.minYear ?? null,
                maxYear: options.maxYear ?? null,
                noFuture: options.noFuture || false,
                locale: options.locale || 'ru',
                onSelect: options.onSelect
            };
            createCalendar(input, opts);
        },
        getValue: (selector) => {
            const input = typeof selector === 'string' ? document.querySelector(selector) : selector;
            const instance = instances.get(input);
            return instance ? instance.selectedDate() : null;
        },
        setValue: (selector, date) => {
            const input = typeof selector === 'string' ? document.querySelector(selector) : selector;
            const instance = instances.get(input);
            if (instance) {
                instance.setDate(date);
            }
        },
        close: (selector) => {
            const input = typeof selector === 'string' ? document.querySelector(selector) : selector;
            const instance = instances.get(input);
            if (instance) {
                instance.calendar.style.display = 'none';
            }
        }
    };
})();

if (typeof window !== 'undefined') {
    window.DatePicker = DatePicker;
}

/* ============================================
   ТУЛТИПЫ (Всплывающие подсказки)
   ============================================
   
   Использование:
   
   1. HTML атрибут:
      <button data-tooltip="Подсказка">Наведите на меня</button>
      <span data-tooltip="Дополнительная информация" data-tooltip-position="top">?</span>
   
   2. Программно:
      Tooltip.init('#myElement', {
        text: 'Текст подсказки',
        position: 'top'  // 'top', 'bottom', 'left', 'right'
      });
*/

const Tooltip = (() => {
    function init(selector, options = {}) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (!element) return;

        const text = options.text || element.getAttribute('data-tooltip') || '';
        const position = options.position || element.getAttribute('data-tooltip-position') || 'top';

        if (!text) return;

        element.classList.add('tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = `tooltip-content ${position}`;
        tooltip.textContent = text;
        element.appendChild(tooltip);

        element.addEventListener('mouseenter', () => {
            element.setAttribute('data-tooltip-visible', 'true');
        });

        element.addEventListener('mouseleave', () => {
            element.removeAttribute('data-tooltip-visible');
        });
    }

    // Автоинициализация для элементов с data-tooltip
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            init(el);
        });
    });

    return { init };
})();