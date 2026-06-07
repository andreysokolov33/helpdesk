/**
 * CHAT CORE: Фундамент приложения
 */
// Используем существующий ChatApp или создаем новый
window.ChatApp = window.ChatApp || {};

window.ChatApp.API_BASE = "/api/v1/helpdesk/chats";
window.ChatApp.MEDIA_URL = "";

window.ChatApp.STATE = {
    currentChatId: null,
    chatsOffset: 0,
    msgsOffset: 0,
    searchQuery: "",
    editingMsgId: null,
    editingAttachments: null,
    editingAttachmentsToDelete: null,
    selectedFile: null,
    ticketMode: false,
    selectedTicketMsgs: new Set(),
    isChatsLoading: false,
    lastSync: Date.now() / 1000,
    lastMessageISO: null,
    lastMessageId: null,
    msgsLoading: false,
    replyToMsgId: null,
    windowedMode: false,
    minLoadedId: null,
    maxLoadedId: null,
    msgPollTimer: null,
    searchTimeout: null
};

// Кэширование UI
window.ChatApp.UI = {
    chatList: document.getElementById("chat-list"),
    chatHeader: document.getElementById("chat-header"),
    messagesContainer: document.getElementById("chat-messages-container"),
    messagesList: document.getElementById("chat-messages"),
    loadMoreChatsWrapper: document.getElementById("load-more-chats"),
    loadMoreChatsBtn: document.getElementById("load-more-chats-btn"),
    loadMoreCompactBtn: document.getElementById("load-more-compact-btn"),
    loadMoreMsgsBtn: document.getElementById("load-more"),
    loadMoreSentinel: document.getElementById("chat-load-more-sentinel"),
    messageContextMenu: document.getElementById("messageContextMenu"),
    replyStrip: document.getElementById("chat-reply-strip"),
    replyAuthor: document.getElementById("chat-reply-author"),
    replyText: document.getElementById("chat-reply-text"),
    replyCloseBtn: document.getElementById("chat-reply-close"),
    form: document.getElementById("chat-form"),
    input: document.getElementById("chat-input"),
    sendBtn: document.querySelector(".send-btn"),
    cancelEditBtn: document.getElementById("cancel-edit"),
    fileInput: document.getElementById("chat-file"),
    filePreview: document.getElementById("file-preview"),
    filePreviewGrid: document.getElementById("file-preview-grid"),
    removeAllFilesBtn: document.getElementById("remove-all-files"),
    searchInput: document.getElementById("chat-search"),
    infoPanel: document.getElementById("user-info-panel"),
    infoContent: document.getElementById("user-info-content"),
    closeInfoBtn: document.getElementById("close-info-btn"),
    deleteModal: document.querySelector(".delete-modal"),
    inputArea: document.querySelector(".chat-input-area"),
    sidebar: document.querySelector(".chat-sidebar"),
    main: document.querySelector(".chat-main"),
    loadNewerSentinel: document.getElementById("chat-load-newer-sentinel"),
    scrollToBottomBtn: document.getElementById("chat-scroll-to-bottom-btn"),
    uploadProgressWrap: document.getElementById("upload-progress-wrap"),
    uploadProgressFill: document.querySelector(".upload-progress-fill"),
    uploadFilesN: document.getElementById("upload-files-n"),
    uploadFilesTotal: document.getElementById("upload-files-total"),
    uploadMbN: document.getElementById("upload-mb-n"),
    uploadMbTotal: document.getElementById("upload-mb-total"),
    uploadSpeed: document.getElementById("upload-speed")
};

window.ChatApp.Utils = {
    escapeHtml(text) {
        if (!text) return "";
        return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    },

    /** Превью цитаты: без сырого HTML в полоске «ответ на». */
    plainTextReplySnippet(s, maxLen = 80) {
        if (s == null || s === "") return "";
        let t = String(s).replace(/<[^>]+>/g, " ");
        t = t
            .replace(/&nbsp;/gi, " ")
            .replace(/&amp;/g, "&")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&quot;/g, '"')
            .replace(/&#039;/g, "'")
            .replace(/\s+/g, " ")
            .trim();
        if (t.length > maxLen) t = t.slice(0, maxLen - 1).replace(/\s+\S*$/, "") + "…";
        return t;
    },

    getInitials(fullname) {
        if (!fullname || !fullname.trim()) return "?";
        const parts = fullname.trim().split(/\s+/).filter(Boolean);
        if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        return fullname.slice(0, 2).toUpperCase();
    },

    formatDateTime(dateStr) {
        if (!dateStr) return "";

        // 1. Создаем объект даты
        // Если в строке есть 'Z' или 'T', Date() автоматически поймет, что это UTC
        let d = new Date(dateStr);

        // 2. Если формат даты был старый (RU), помогаем парсеру
        if (isNaN(d.getTime()) && dateStr.includes('.')) {
            const match = dateStr.match(/^(\d{2})\.(\d{2})\.(\d{4})\s(\d{2}):(\d{2})/);
            if (match) {
                // Форсируем UTC через Date.UTC
                d = new Date(Date.UTC(+match[3], +match[2] - 1, +match[1], +match[4], +match[5]));
            }
        }

        if (isNaN(d.getTime())) return dateStr;

        // 3. Получаем локальные значения (браузер сам прибавит нужные часы)
        const now = new Date();
        const isToday = d.toDateString() === now.toDateString();

        const pad = (n) => n.toString().padStart(2, '0');
        const HH = pad(d.getHours());
        const mm = pad(d.getMinutes());
        const DD = pad(d.getDate());
        const MM = pad(d.getMonth() + 1);

        // Если сообщение сегодня — пишем только время, если раньше — дату и время
        return isToday ? `${HH}:${mm}` : `${DD}.${MM} ${HH}:${mm}`;
    },

    formatTraffic(val) {
        if (val == null) return "0 МБ";
        return Math.round(parseFloat(val)).toLocaleString('ru-RU') + " МБ";
    },

    scrollToBottom(forceDuration = 0) {
        const container = window.ChatApp.UI.messagesContainer;
        if (!container) return;
        const doScroll = () => { container.scrollTop = container.scrollHeight; };
        doScroll();
        if (forceDuration > 0) {
            const startTime = performance.now();
            const loop = (currentTime) => {
                doScroll();
                if (currentTime - startTime < forceDuration) requestAnimationFrame(loop);
            };
            requestAnimationFrame(loop);
        }
    },

    getISOTimestamp(dateStr) {
        if (!dateStr) return null;
        // Если дата уже ISO (содержит T), просто возвращаем её
        if (dateStr.includes('T')) return dateStr;

        // Если дата RU "22.01.2026 08:42"
        const matchRu = dateStr.match(/^(\d{2})\.(\d{2})\.(\d{4})\s(\d{2}):(\d{2})/);
        if (matchRu) {
            const [_, d, m, y, hh, mm] = matchRu;
            return `${y}-${m}-${d}T${hh}:${mm}:00Z`;
        }
        return dateStr;
    },
    // Получаем текущее время в секундах + 3 часа (для БД)
    getMoscowSeconds() {
        // Чистый UTC Timestamp
        return Math.floor(Date.now() / 1000);
    },
    isMobile() {
        return window.innerWidth <= 768;
    },
    /**
     * Возвращает строку-подпись для даты сообщения
     * @param {string} isoDate - ISO-строка или RU-формат "22.01.2026 08:42"
     * @returns {string|null}
    */
    getDateLabel(isoDate) {
        if (!isoDate) return null;

        // Приводим к Date
        let d = new Date(isoDate);
        if (isNaN(d.getTime()) && isoDate.includes('.')) {
            const match = isoDate.match(/^(\d{2})\.(\d{2})\.(\d{4})/);
            if (match) {
                d = new Date(Date.UTC(+match[3], +match[2] - 1, +match[1]));
            }
        }
        if (isNaN(d.getTime())) return null;

        // Нормализуем до UTC-дня (чтобы избежать смещения из-за часовых поясов)
        const msgDay = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
        const now = new Date();
        const today = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
        const yesterday = new Date(today);
        yesterday.setUTCDate(yesterday.getUTCDate() - 1);

        if (msgDay.getTime() === today.getTime()) return "Сегодня";
        if (msgDay.getTime() === yesterday.getTime()) return "Вчера";

        const currentYear = now.getFullYear();
        const msgYear = msgDay.getUTCFullYear();
        if (msgYear === currentYear) {
            return msgDay.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
        }
        return msgDay.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
    },
};

console.log("ChatApp Core initialized");