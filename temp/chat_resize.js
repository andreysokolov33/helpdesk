/**
 * Resizable chat sidebar — перетаскивание границы, сохранение в localStorage
 */
(function () {
    const STORAGE_KEY = 'chat_sidebar_width';
    const MIN_WIDTH = 72;
    const MAX_WIDTH = 480;
    const COMPACT_THRESHOLD = 120;
    const DEFAULT_WIDTH = 320;

    function getLayout() {
        return document.querySelector('.chat-layout');
    }
    function getSidebar() {
        return document.querySelector('.chat-sidebar');
    }
    function getHandle() {
        return document.getElementById('chat-resize-handle');
    }

    function loadStoredWidth() {
        try {
            const w = parseInt(localStorage.getItem(STORAGE_KEY), 10);
            if (w >= MIN_WIDTH && w <= MAX_WIDTH) return w;
        } catch (_) {}
        return DEFAULT_WIDTH;
    }

    function saveWidth(width) {
        try {
            localStorage.setItem(STORAGE_KEY, String(width));
        } catch (_) {}
    }

    function applyWidth(width) {
        const layout = getLayout();
        const sidebar = getSidebar();
        if (!layout || !sidebar) return;
        const clamped = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
        layout.style.setProperty('--chat-sidebar-width', clamped + 'px');
        sidebar.classList.toggle('compact', clamped < COMPACT_THRESHOLD);
    }

    function initResize() {
        const handle = getHandle();
        const layout = getLayout();
        const sidebar = getSidebar();
        if (!handle || !layout || !sidebar) return;

        if (window.innerWidth <= 768) return;

        const stored = loadStoredWidth();
        applyWidth(stored);

        let startX = 0;
        let startWidth = 0;

        handle.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            const w = layout.style.getPropertyValue('--chat-sidebar-width');
            startWidth = w ? parseInt(w, 10) : DEFAULT_WIDTH;
            startX = e.clientX;
            handle.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';

            const onMove = (ev) => {
                const delta = ev.clientX - startX;
                const newWidth = startWidth + delta;
                applyWidth(newWidth);
            };
            const onUp = () => {
                handle.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                const w = layout.style.getPropertyValue('--chat-sidebar-width');
                if (w) saveWidth(parseInt(w, 10));
            };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initResize);
    } else {
        initResize();
    }
})();
