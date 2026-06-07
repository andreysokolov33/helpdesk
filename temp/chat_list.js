/**
 * CHAT LIST: Исправленная версия с гарантированным обновлением lastSync
 */
(function (App) {
    if (!App) return console.error("ChatApp Core not found!");
    const { UI, STATE, Utils } = App;

    App.List = {
        pollInterval: null,

        async init() {
            // Фильтр «только непрочитанные» по умолчанию выключен (показываем все чаты)
            STATE.unreadOnly = false;
            // Инициализируем метку текущим временем сразу
            STATE.lastSync = Utils.getMoscowSeconds();

            await this.loadChats(true);
            this.startPolling();
            this.bindEvents();

            await this.loadChats(true);
            this.startPolling();
            this.bindEvents();

            // === ОБРАБОТКА direct_user_id ===
            const urlParams = new URLSearchParams(window.location.search);
            const directUserId = urlParams.get('direct_user_id');
            if (directUserId && /^\d+$/.test(directUserId)) {
                const newUrl = new URL(window.location);
                newUrl.searchParams.delete('direct_user_id');
                window.history.replaceState({}, '', newUrl);

                try {
                    let chat = null;
                    const searchRes = await fetch(`${App.API_BASE}/search?query=${directUserId}&limit=1`);
                    if (searchRes.ok) {
                        const chats = await searchRes.json();
                        if (chats.length > 0) chat = chats[0];
                    }
                    if (!chat) {
                        const createRes = await fetch(`${App.API_BASE}/find-or-create?user_id=${directUserId}`);
                        if (createRes.ok) chat = await createRes.json();
                    }
                    if (chat) {
                        App.Messages.openChat(chat.chat_id, chat.fullname, Number(chat.is_online) === 1);
                    } else {
                        DarkToast.error("Пользователь не найден");
                    }
                } catch (e) {
                    console.error("Ошибка открытия чата:", e);
                    DarkToast.error("Не удалось открыть чат");
                }
            }

            // Открытие чата по ссылке ?chat=123 или ?chat=123#msg-456
            const chatIdFromUrl = urlParams.get('chat');
            if (chatIdFromUrl && /^\d+$/.test(chatIdFromUrl)) {
                const btn = UI.chatList.querySelector(`button[data-chat-id="${chatIdFromUrl}"]`);
                if (btn) {
                    document.querySelectorAll("#chat-list button").forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    App.Messages.openChat(btn.dataset.chatId, btn.dataset.name, Number(btn.dataset.online) === 1);
                }
            }

        },

        async loadChats(reset = false) {
            if (STATE.isChatsLoading) return;
            STATE.isChatsLoading = true;

            if (reset) {
                UI.chatList.innerHTML = "";
                STATE.chatsOffset = 0;
                // Не сбрасываем в 0, всегда держим актуальное время
                STATE.lastSync = Utils.getMoscowSeconds();
            }

            try {
                const url = STATE.searchQuery
                    ? `${App.API_BASE}/search?query=${encodeURIComponent(STATE.searchQuery)}&limit=20`
                    : `${App.API_BASE}/all?limit=15&offset=${STATE.chatsOffset}`;

                const r = await fetch(url);
                if (!r.ok) throw new Error("Fetch failed");
                const chats = await r.json();

                if (chats.length === 0 && reset) {
                    UI.chatList.innerHTML = '<li style="padding:20px; text-align:center; color:gray">Чаты не найдены</li>';
                    UI.loadMoreChatsWrapper.classList.add("hidden");
                    return;
                }

                chats.forEach(chat => {
                    const li = document.createElement("li");
                    li.innerHTML = this.createItemHTML(chat);
                    UI.chatList.appendChild(li);

                    // Если в базе есть сообщения из будущего (относительно времени загрузки), подтягиваем метку
                    const chatDate = Number(chat.last_message_date);
                    if (!isNaN(chatDate) && chatDate > STATE.lastSync) {
                        STATE.lastSync = chatDate;
                    }
                });

                STATE.chatsOffset += chats.length;
                const hasMore = !STATE.searchQuery && chats.length >= 15;
                UI.loadMoreChatsWrapper.classList.toggle("hidden", !hasMore);

                this.applyUnreadFilter();

            } catch (e) {
                console.error("Load chats error:", e);
            } finally {
                STATE.isChatsLoading = false;
            }
        },

        // Фильтрация списка чатов при активном чекбоксе «только непрочитанные».
        // Видимыми остаются: чаты с непрочитанными, а также текущий открытый чат
        // (чтобы он не пропадал во время чтения; он скроется после выхода из него).
        applyUnreadFilter() {
            const only = !!STATE.unreadOnly;
            UI.chatList.querySelectorAll("li").forEach(li => {
                const btn = li.querySelector("button[data-chat-id]");
                if (!btn || !only) {
                    li.style.display = "";
                    return;
                }
                const isUnread = btn.classList.contains("unread-chat-item");
                const isActive = String(STATE.currentChatId) === String(btn.dataset.chatId);
                li.style.display = (isUnread || isActive) ? "" : "none";
            });
        },

        startPolling() {
            if (this.pollInterval) clearInterval(this.pollInterval);

            this.pollInterval = setInterval(async () => {
                // Если идет поиск или страница скрыта — пропускаем, но метку времени НЕ двигаем,
                // чтобы после возвращения на вкладку забрать всё пропущенное.
                if (STATE.searchQuery || document.hidden || STATE.isChatsLoading) return;

                try {
                    // Запоминаем время, в которое мы отправили запрос
                    const currentRequestTime = Utils.getMoscowSeconds();

                    const r = await fetch(`${App.API_BASE}/updates?last_sync=${STATE.lastSync}`);

                    if (r.ok) {
                        const updates = await r.json();

                        if (updates && updates.length > 0) {
                            // Ищем максимальную дату среди новых сообщений
                            let maxDbDate = 0;
                            updates.forEach(u => {
                                const d = Number(u.last_message_date);
                                if (!isNaN(d) && d > maxDbDate) maxDbDate = d;
                            });

                            // Обновляем метку: либо временем самого нового сообщения, либо временем запроса
                            STATE.lastSync = Math.max(maxDbDate, currentRequestTime);
                            this.processUpdates(updates);
                        } else {
                            // Если новых чатов нет, обязательно двигаем метку к времени запроса.
                            // Это предотвращает повторные запросы за тот же пустой период.
                            STATE.lastSync = currentRequestTime;
                        }

                        // Отладка в консоль (удали потом)
                        console.log("Next poll will use last_sync:", STATE.lastSync);
                    }
                } catch (e) {
                    console.warn("Polling error:", e);
                }
            }, 10000); // 10 секунд
        },

        processUpdates(updates) {
            [...updates].reverse().forEach(chat => {
                const existingBtn = UI.chatList.querySelector(`button[data-chat-id="${chat.chat_id}"]`);
                if (existingBtn) {
                    existingBtn.closest('li').remove();
                }
                const li = document.createElement("li");
                li.innerHTML = this.createItemHTML(chat);
                UI.chatList.prepend(li);
            });
            this.applyUnreadFilter();
        },

        bindEvents() {
            UI.searchInput.addEventListener("input", (e) => {
                const val = e.target.value.trim();
                clearTimeout(STATE.searchTimeout);
                STATE.searchTimeout = setTimeout(() => {
                    STATE.searchQuery = val;
                    this.loadChats(true);
                }, 500);
            });

            UI.loadMoreChatsBtn.onclick = () => this.loadChats(false);
            if (UI.loadMoreCompactBtn) UI.loadMoreCompactBtn.onclick = () => this.loadChats(false);

            const unreadToggle = document.getElementById("chat-unread-only");
            if (unreadToggle) {
                unreadToggle.addEventListener("change", (e) => {
                    STATE.unreadOnly = e.target.checked;
                    this.applyUnreadFilter();
                });
            }

            UI.chatList.onclick = (e) => {
                const btn = e.target.closest("button[data-chat-id]");
                if (!btn) return;
                document.querySelectorAll("#chat-list button").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                App.Messages.openChat(btn.dataset.chatId, btn.dataset.name, Number(btn.dataset.online) === 1);
            };
        },

        createItemHTML(chat) {
            const hasUnread = Number(chat.unread_count) > 0;
            const isOnline = Number(chat.is_online) === 1;
            const jurClass = chat.is_jur ? 'is-jur' : '';
            const unreadClass = hasUnread ? 'unread-chat-item' : '';
            const activeClass = STATE.currentChatId == chat.chat_id ? 'active' : '';
            const dateStr = chat.last_message_date_iso || chat.formatted_date;
            const timeDisplay = Utils.formatDateTime(dateStr);
            const lastMsg = (chat.last_message_text || '').trim();
            const lastMsgTruncated = lastMsg.length > 40 ? lastMsg.slice(0, 37) + '...' : lastMsg;
            const lastMsgTitle = lastMsg ? Utils.escapeHtml(lastMsg) : '';
            const initials = Utils.getInitials(chat.fullname);
            const avatarJurClass = chat.is_jur ? ' jur' : '';

            return `
                <button data-chat-id="${chat.chat_id}" 
                        data-name="${Utils.escapeHtml(chat.fullname)}" 
                        data-online="${chat.is_online}"
                        class="${unreadClass} ${activeClass}">
                    <div class="chat-item-compact">
                        <span class="chat-avatar-initials ${avatarJurClass}" title="${Utils.escapeHtml(chat.fullname)}">
                            ${initials}
                            <span class="online-indicator ${isOnline ? 'online' : 'offline'}"></span>
                        </span>
                    </div>
                    <div class="chat-item chat-item-full">
                        <div class="chat-name-wrapper">
                            <span class="online-indicator ${isOnline ? 'online' : 'offline'}"></span>
                            <span class="chat-fullname ${jurClass}">${Utils.escapeHtml(chat.fullname)}</span>
                        </div>
                        <div class="chat-meta">
                            <span class="chat-date">${timeDisplay}</span>
                            ${lastMsgTruncated ? `<span class="chat-last-msg" title="${lastMsgTitle}">${Utils.escapeHtml(lastMsgTruncated)}</span>` : ''}
                            ${hasUnread ? `<span class="unread-badge">${chat.unread_count}</span>` : ''}
                        </div>
                        <div class="chat-station-row">
                            ${chat.top_subscriber_rank ? `<span class="top-subscriber-rank-badge" title="ТОП-50 абонент, место ${chat.top_subscriber_rank}">${chat.top_subscriber_rank}</span>` : ''}
                            <span class="chat-station">${Utils.escapeHtml(chat.station_name || '')}</span>
                        </div>
                    </div>
                </button>`;
        },

        moveChatToTop(chatId) {
            const btn = UI.chatList.querySelector(`button[data-chat-id="${chatId}"]`);
            if (btn) {
                const li = btn.closest("li");
                if (UI.chatList.firstChild !== li) {
                    UI.chatList.prepend(li);
                }
            }
        },
        // Внутри App.Messages
        shouldInsertTodayDivider() {
            // Получаем последнее сообщение в DOM
            const lastMsg = UI.messagesList.lastElementChild;

            // Если нет сообщений — вставляем всегда
            if (!lastMsg) return true;

            // Если последний элемент — не сообщение (например, empty-chat), то тоже вставляем
            if (!lastMsg.classList.contains('message')) return true;

            // Проверяем дату последнего сообщения
            const lastMsgDate = lastMsg.querySelector('.time')?.textContent;
            if (!lastMsgDate) return true;

            // Определяем, сегодня ли оно
            const now = new Date();
            const isToday = lastMsgDate.match(/^\d{2}:\d{2}$/); // только время → сегодня

            // Если последнее сообщение НЕ сегодня — нужен разделитель
            return !isToday;
        },
        // Внутри App.Messages
        getDateLabelByMessage(msgEl) {
            // Извлекаем дату из элемента сообщения
            const timeEl = msgEl.querySelector('.time');
            if (!timeEl) return null;

            const timeText = timeEl.textContent;
            if (!timeText) return null;

            // Определяем дату:
            // - Если формат "HH:MM" → сегодня
            // - Если "DD.MM" → вчера или старше
            // Но у нас нет полной даты в DOM!

            // Поэтому сохраняем дату в data-атрибут при создании сообщения (лучший способ)
            return msgEl.dataset.dateLabel || null;
        },
        // Обновляет состояние чата в списке (убирает выделение и счётчик)
        updateChatReadStatus(chatId) {
            const btn = UI.chatList.querySelector(`button[data-chat-id="${chatId}"]`);
            if (!btn) return;

            // Убираем классы
            btn.classList.remove('unread-chat-item');

            // Убираем счётчик
            const badge = btn.querySelector('.unread-badge');
            if (badge) {
                badge.textContent = '';
                badge.classList.add('hidden');
            }
        },

        // В chat_list.js, внутри App.List
        async findOrCreateChatByUserId(userId) {
            try {
                const r = await fetch(`${App.API_BASE}/find-or-create?user_id=${userId}`);
                if (!r.ok) throw new Error("Chat not found");
                const chat = await r.json();
                return chat;
            } catch (e) {
                DarkToast.error("Не удалось открыть чат с пользователем");
                return null;
            }
        },
    };

    document.addEventListener("DOMContentLoaded", () => App.List.init());
})(window.ChatApp);