import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import MessageBody from "@/components/MessageBody";
import FileBadge, { resolveFileExt, truncateFilename } from "@/components/FileBadge";
import ChatMessageContextMenu, { type ChatMenuAction } from "@/components/ChatMessageContextMenu";
import TicketChatScrollDown from "@/components/TicketChatScrollDown";
import { fetchAuthMe } from "@/api/auth";
import { formatDateTimeLocal } from "@/utils/dateTime";
import { formatBytes } from "@/utils/formatBytes";
import {
  deleteChatMessage,
  editChatMessage,
  fetchChatMessageUpdates,
  fetchChatMessages,
  fetchChatReadReceipts,
  fetchChatUpdates,
  fetchChats,
  markChatRead,
  mergeChatMessages,
  searchChats,
  sendChatMessage,
  type ChatListItem,
  type ChatMessage,
} from "@/api/chat";
import {
  CHAT_SCROLL_EDGE_PX,
  isChatAtBottom,
  scrollChatToBottom,
  watchChatScrollToBottom,
} from "@/utils/ticketChatScroll";
import "@/styles/chat-section.css";

const CHATS_POLL_MS = 10_000;
const MSG_POLL_MS = 8_000;
const READ_POLL_MS = 4_000;
const AUTO_READ_DELAY_MS = 3_000;
const PAGE_SIZE = 20;
const CHATS_PAGE_SIZE = 30;

function initials(name: string): string {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return (name || "?").slice(0, 2).toUpperCase();
}

function chatTime(iso?: string | null): string {
  return formatDateTimeLocal(iso) || "";
}

function maxId(list: ChatMessage[]): number {
  return list.reduce((m, x) => (x.msg_id > m ? x.msg_id : m), 0);
}

function minId(list: ChatMessage[]): number | null {
  if (!list.length) return null;
  return list.reduce((m, x) => (x.msg_id < m ? x.msg_id : m), list[0].msg_id);
}

function isAllowedChatImage(file: File): boolean {
  if (file.type && file.type.startsWith("image/")) return true;
  const ext = (file.name || "").split(".").pop()?.toLowerCase();
  return ext === "jpg" || ext === "jpeg" || ext === "png" || ext === "gif" || ext === "webp" || ext === "bmp";
}

function plainPreview(text: string): string {
  const t = (text || "").replace(/<[^>]+>/g, " ");
  const doc = t
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
  return doc;
}

export default function ChatSectionPage() {
  const [params, setParams] = useSearchParams();
  const activeId = Number(params.get("id")) || 0;

  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [chatsLoading, setChatsLoading] = useState(true);
  const [chatsHasMore, setChatsHasMore] = useState(false);
  const [chatsLoadingMore, setChatsLoadingMore] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<ChatListItem[] | null>(null);
  const lastSyncRef = useRef<number>(Math.floor(Date.now() / 1000));

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [msgLoading, setMsgLoading] = useState(false);
  const [hasOlder, setHasOlder] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [readBy, setReadBy] = useState<Record<number, boolean>>({});

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null);
  const [replyTo, setReplyTo] = useState<ChatMessage | null>(null);
  const [editing, setEditing] = useState<ChatMessage | null>(null);
  const [lightbox, setLightbox] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; msg: ChatMessage } | null>(null);
  const [viewerId, setViewerId] = useState<number | null>(null);
  const [atBottom, setAtBottom] = useState(true);
  const [pendingNewCount, setPendingNewCount] = useState(0);

  const scrollRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const messagesRef = useRef<ChatMessage[]>([]);
  const atBottomRef = useRef(true);
  const loadingOlderRef = useRef(false);
  const pendingScrollToBottomRef = useRef(false);
  const initialScrollCleanupRef = useRef<(() => void) | null>(null);
  const didInitialAutoscrollRef = useRef(false);
  const activeChat = useMemo(
    () => chats.find((c) => c.chat_id === activeId) ?? null,
    [chats, activeId],
  );

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    if (!file) {
      setFilePreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setFilePreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function clearAttachedFile() {
    setFile(null);
  }

  function attachImage(next: File) {
    if (!isAllowedChatImage(next)) {
      window.alert("Можно прикрепить только изображение (JPG, PNG, GIF, WebP, BMP).");
      return;
    }
    setInput("");
    setFile(next);
  }

  // ── Список чатов: первичная загрузка ───────────────────────────────────────
  const loadChats = useCallback(async () => {
    setChatsLoading(true);
    try {
      const data = await fetchChats(CHATS_PAGE_SIZE, 0);
      setChats(data);
      setChatsHasMore(data.length >= CHATS_PAGE_SIZE);
      lastSyncRef.current = Math.floor(Date.now() / 1000);
    } catch {
      setChats([]);
      setChatsHasMore(false);
    } finally {
      setChatsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadChats();
  }, [loadChats]);

  useEffect(() => {
    fetchAuthMe()
      .then((me) => setViewerId(me.user_id))
      .catch(() => setViewerId(null));
  }, []);

  const loadMoreChats = useCallback(async () => {
    if (chatsLoadingMore || !chatsHasMore) return;
    setChatsLoadingMore(true);
    try {
      const data = await fetchChats(CHATS_PAGE_SIZE, chats.length);
      setChats((prev) => {
        const map = new Map(prev.map((c) => [c.chat_id, c]));
        for (const c of data) if (!map.has(c.chat_id)) map.set(c.chat_id, c);
        return Array.from(map.values());
      });
      setChatsHasMore(data.length >= CHATS_PAGE_SIZE);
    } catch {
      /* тихо */
    } finally {
      setChatsLoadingMore(false);
    }
  }, [chats.length, chatsHasMore, chatsLoadingMore]);

  // ── Поллинг списка: новые/обновлённые чаты ────────────────────────────────
  useEffect(() => {
    const merge = async () => {
      try {
        const updates = await fetchChatUpdates(lastSyncRef.current);
        lastSyncRef.current = Math.floor(Date.now() / 1000);
        if (!updates.length) return;
        setChats((prev) => {
          const map = new Map(prev.map((c) => [c.chat_id, c]));
          for (const u of updates) map.set(u.chat_id, u);
          return Array.from(map.values()).sort((a, b) => {
            if (Boolean(a.has_unread) !== Boolean(b.has_unread)) return a.has_unread ? -1 : 1;
            return (b.last_message_date_iso || "").localeCompare(a.last_message_date_iso || "");
          });
        });
      } catch {
        /* поллинг не мешает работе */
      }
    };
    const id = window.setInterval(() => void merge(), CHATS_POLL_MS);
    return () => window.clearInterval(id);
  }, []);

  // ── Поиск (debounce) ──────────────────────────────────────────────────────
  useEffect(() => {
    const q = searchInput.trim();
    if (!q) {
      setSearchResults(null);
      return;
    }
    const t = window.setTimeout(async () => {
      try {
        setSearchResults(await searchChats(q, 30));
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  const baseChats = searchResults ?? chats;
  const visibleChats = unreadOnly ? baseChats.filter((c) => c.has_unread) : baseChats;

  function selectChat(id: number) {
    const next = new URLSearchParams(params);
    next.set("id", String(id));
    setParams(next);
  }

  function backToList() {
    const next = new URLSearchParams(params);
    next.delete("id");
    setParams(next);
  }

  // ── Загрузка сообщений выбранного чата ────────────────────────────────────
  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    setMsgLoading(true);
    setReplyTo(null);
    setEditing(null);
    setContextMenu(null);
    setFile(null);
    setInput("");
    setAtBottom(true);
    setPendingNewCount(0);
    atBottomRef.current = true;
    pendingScrollToBottomRef.current = false;
    didInitialAutoscrollRef.current = false;
    initialScrollCleanupRef.current?.();
    initialScrollCleanupRef.current = null;
    (async () => {
      try {
        const res = await fetchChatMessages(activeId, { limit: PAGE_SIZE });
        if (cancelled) return;
        const sorted = [...res.messages].sort((a, b) => a.msg_id - b.msg_id);
        setMessages(sorted);
        setHasOlder(Boolean(res.has_older));
        pendingScrollToBottomRef.current = true;
        atBottomRef.current = true;
        setAtBottom(true);
      } catch {
        if (!cancelled) {
          setMessages([]);
          setHasOlder(false);
        }
      } finally {
        if (!cancelled) setMsgLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      initialScrollCleanupRef.current?.();
      initialScrollCleanupRef.current = null;
    };
  }, [activeId]);

  // ── Поллинг новых сообщений в открытом чате ───────────────────────────────
  useEffect(() => {
    if (!activeId) return;
    const poll = async () => {
      const since = maxId(messagesRef.current);
      if (since <= 0) return;
      try {
        const incoming = await fetchChatMessageUpdates(activeId, since);
        if (!incoming.length) return;
        setMessages((prev) => mergeChatMessages(prev, incoming));
        if (atBottomRef.current) {
          pendingScrollToBottomRef.current = true;
          setPendingNewCount(0);
        } else {
          setPendingNewCount((c) => c + incoming.length);
        }
      } catch {
        /* тихо */
      }
    };
    const id = window.setInterval(() => void poll(), MSG_POLL_MS);
    return () => window.clearInterval(id);
  }, [activeId]);

  // ── Поллинг галочек прочтения для исходящих ───────────────────────────────
  useEffect(() => {
    if (!activeId) return;
    const poll = async () => {
      const outgoingIds = messagesRef.current
        .filter((m) => m.answer && !readBy[m.msg_id])
        .map((m) => m.msg_id);
      if (!outgoingIds.length) return;
      try {
        const receipts = await fetchChatReadReceipts(activeId, outgoingIds);
        const next: Record<number, boolean> = {};
        for (const [id, readers] of Object.entries(receipts)) {
          if (readers.some((r) => r.person_type === "user")) next[Number(id)] = true;
        }
        if (Object.keys(next).length) setReadBy((prev) => ({ ...prev, ...next }));
      } catch {
        /* тихо */
      }
    };
    void poll();
    const id = window.setInterval(() => void poll(), READ_POLL_MS);
    return () => window.clearInterval(id);
  }, [activeId, readBy]);

  // ── Авто-отметка прочтения входящих ───────────────────────────────────────
  useEffect(() => {
    if (!activeId) return;
    const t = window.setTimeout(async () => {
      const unreadIncoming = messagesRef.current
        .filter((m) => !m.answer && !m.has_read)
        .map((m) => m.msg_id);
      if (!unreadIncoming.length) return;
      try {
        await markChatRead(activeId, unreadIncoming);
        setMessages((prev) =>
          prev.map((m) => (unreadIncoming.includes(m.msg_id) ? { ...m, has_read: true } : m)),
        );
        setChats((prev) =>
          prev.map((c) =>
            c.chat_id === activeId ? { ...c, has_unread: false, unread_count: 0 } : c,
          ),
        );
      } catch {
        /* тихо */
      }
    }, AUTO_READ_DELAY_MS);
    return () => window.clearTimeout(t);
  }, [activeId, messages]);

  // ── Подгрузка истории при прокрутке вверх ─────────────────────────────────
  const loadOlder = useCallback(async () => {
    if (!activeId || !hasOlder || loadingOlderRef.current) return;
    const before = minId(messagesRef.current);
    if (before == null) return;
    const el = scrollRef.current;
    if (!el) return;
    loadingOlderRef.current = true;
    setLoadingOlder(true);
    const prevHeight = el.scrollHeight;
    const prevTop = el.scrollTop;
    try {
      const res = await fetchChatMessages(activeId, { limit: PAGE_SIZE, beforeId: before });
      setHasOlder(Boolean(res.has_older) && res.messages.length > 0);
      setMessages((prev) => mergeChatMessages(prev, res.messages));
      requestAnimationFrame(() => {
        const box = scrollRef.current;
        if (box) box.scrollTop = box.scrollHeight - prevHeight + prevTop;
      });
    } catch {
      /* тихо */
    } finally {
      loadingOlderRef.current = false;
      setLoadingOlder(false);
    }
  }, [activeId, hasOlder]);

  useEffect(() => {
    const root = scrollRef.current;
    const target = topSentinelRef.current;
    if (!root || !target) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) void loadOlder();
      },
      { root, threshold: 0 },
    );
    obs.observe(target);
    return () => obs.disconnect();
  }, [loadOlder, activeId]);

  useLayoutEffect(() => {
    if (didInitialAutoscrollRef.current) return;
    if (!activeId || msgLoading) return;
    const el = scrollRef.current;
    if (!el || !messages.length) return;

    initialScrollCleanupRef.current?.();
    initialScrollCleanupRef.current = watchChatScrollToBottom(el);
    didInitialAutoscrollRef.current = true;
    atBottomRef.current = true;
    setAtBottom(true);
    setPendingNewCount(0);

    return () => {
      initialScrollCleanupRef.current?.();
      initialScrollCleanupRef.current = null;
    };
  }, [activeId, msgLoading, messages.length]);

  useLayoutEffect(() => {
    if (!pendingScrollToBottomRef.current) return;
    const el = scrollRef.current;
    if (!el) return;
    pendingScrollToBottomRef.current = false;
    scrollChatToBottom(el);
  }, [messages]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const bottom = isChatAtBottom(el, CHAT_SCROLL_EDGE_PX);
      atBottomRef.current = bottom;
      setAtBottom(bottom);
      if (bottom) setPendingNewCount(0);
    };
    onScroll();
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [activeId]);

  const goToChatBottom = useCallback(() => {
    atBottomRef.current = true;
    setAtBottom(true);
    setPendingNewCount(0);
    pendingScrollToBottomRef.current = true;
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) scrollChatToBottom(el);
    });
  }, []);

  // ── Отправка / редактирование ──────────────────────────────────────────────
  async function handleSend() {
    if (!activeId) return;
    const text = input.trim();

    if (editing) {
      if (!text) return;
      setSending(true);
      try {
        await editChatMessage(activeId, editing.msg_id, text);
        setMessages((prev) =>
          prev.map((m) => (m.msg_id === editing.msg_id ? { ...m, text } : m)),
        );
        setEditing(null);
        setInput("");
      } catch (e) {
        window.alert(e instanceof Error ? e.message : "Не удалось сохранить изменения");
      } finally {
        setSending(false);
      }
      return;
    }

    if (!text && !file) return;
    if (text && file) {
      window.alert("Отправьте текст или изображение, но не оба одновременно.");
      return;
    }
    setSending(true);
    try {
      const wasAtBottom = atBottomRef.current;
      const created = await sendChatMessage(activeId, text, file, replyTo?.msg_id ?? null);
      setMessages((prev) => mergeChatMessages(prev, [created]));
      setInput("");
      clearAttachedFile();
      setReplyTo(null);
      if (wasAtBottom) {
        atBottomRef.current = true;
        setAtBottom(true);
        setPendingNewCount(0);
        pendingScrollToBottomRef.current = true;
      } else {
        setPendingNewCount((c) => c + 1);
      }
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Не удалось отправить сообщение");
    } finally {
      setSending(false);
    }
  }

  async function handleDelete(msg: ChatMessage) {
    if (!activeId) return;
    if (!window.confirm("Удалить сообщение?")) return;
    try {
      await deleteChatMessage(activeId, msg.msg_id);
      setMessages((prev) => prev.filter((m) => m.msg_id !== msg.msg_id));
      if (editing?.msg_id === msg.msg_id) {
        setEditing(null);
        setInput("");
      }
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Не удалось удалить");
    }
  }

  function handleMenuAction(action: ChatMenuAction, msg: ChatMessage) {
    setContextMenu(null);
    if (action === "copy") {
      const plain = plainPreview(msg.text);
      if (plain) void navigator.clipboard.writeText(plain).catch(() => {});
      return;
    }
    if (action === "reply") {
      setEditing(null);
      setReplyTo(msg);
      return;
    }
    if (action === "edit") {
      setReplyTo(null);
      setEditing(msg);
      setInput(plainPreview(msg.text));
      return;
    }
    if (action === "delete") {
      void handleDelete(msg);
    }
  }

  function renderChatItem(c: ChatListItem) {
    return (
      <button
        key={c.chat_id}
        type="button"
        className={`cs-chat${c.chat_id === activeId ? " is-active" : ""}${c.has_unread ? " is-unread" : ""}`}
        onClick={() => selectChat(c.chat_id)}
      >
        <span className={`cs-chat__av${c.is_jur ? " cs-chat__av--jur" : ""}`}>
          {initials(c.fullname)}
          <span className={`cs-chat__dot${c.is_online ? " is-online" : ""}`} />
        </span>
        <span className="cs-chat__name" title={c.fullname}>
          {c.fullname}
        </span>
        <span className="cs-chat__time">{chatTime(c.last_message_date_iso)}</span>
        <span className="cs-chat__last">{plainPreview(c.last_message_text || "") || "—"}</span>
        {c.has_unread && c.unread_count > 0 ? (
          <span className="cs-chat__badge">{c.unread_count > 99 ? "99+" : c.unread_count}</span>
        ) : null}
      </button>
    );
  }

  function renderMessage(m: ChatMessage) {
    const side = m.answer ? "me" : "cl";
    const kind = m.author_kind || (side === "me" ? "support" : "subscriber");
    const kindCls = side === "me" ? ` k-${kind}` : "";
    const images = m.attachments.filter((a) => a.is_image);
    const files = m.attachments.filter((a) => !a.is_image);
    return (
      <div
        key={m.msg_id}
        data-msg-id={m.msg_id}
        className={`cs-msg ${side}${editing?.msg_id === m.msg_id ? " is-editing" : ""}`}
        onContextMenu={(e) => {
          e.preventDefault();
          setContextMenu({ x: e.clientX, y: e.clientY, msg: m });
        }}
      >
        <div className={`cs-mav ${side === "me" ? "ag" : "cl"}${kindCls}`}>
          {side === "me"
            ? m.whose_message === "Вы"
              ? "Вы"
              : initials(m.whose_message || "О")
            : initials(activeChat?.fullname || "А")}
        </div>
        <div className="cs-mc">
          <div className={`cs-bbl ${side === "me" ? "ag" : "cl"}${kindCls}`}>
            <div className="cs-msg-label">{m.whose_message}</div>
            {m.relay_msg_id && (m.relay_author || m.relay_snippet) ? (
              <div className="cs-quote">
                <div className="cs-quote__author">{m.relay_author || "Сообщение"}</div>
                <div className="cs-quote__text">{m.relay_snippet || ""}</div>
              </div>
            ) : null}
            <MessageBody text={m.text} className="cs-msg-text" />
            {m.attachments.length ? (
              <div className="cs-att">
                {images.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    className="cs-att-img"
                    onClick={() => setLightbox(a.file_path)}
                    title={a.original_filename}
                  >
                    <img src={a.file_path} alt={a.original_filename} loading="lazy" />
                  </button>
                ))}
                {files.map((a) => (
                  <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="cs-att-file">
                    <FileBadge filename={a.original_filename} ext={resolveFileExt(a.original_filename)} />
                    <span className="cs-att-file__name">{truncateFilename(a.original_filename || "Файл")}</span>
                  </a>
                ))}
              </div>
            ) : null}
          </div>
          <div className="cs-mtm">
            <span>{chatTime(m.date_iso) || "—"}</span>
            {m.answer ? (
              <span
                className={`cs-tick${m.subscriber_read_at || readBy[m.msg_id] ? " is-read" : ""}`}
                title={m.subscriber_read_at || readBy[m.msg_id] ? "Прочитано абонентом" : "Доставлено"}
              >
                {m.subscriber_read_at || readBy[m.msg_id] ? "✓✓" : "✓"}
              </span>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="tp on" id="cs-page">
      <div className={`cs-shell${activeId ? " has-active" : ""}`}>
        <aside className="cs-sidebar">
          <div className="cs-sidebar__head">
            <div className="cs-sidebar__title">Чаты с абонентами</div>
            <input
              type="search"
              className="cs-search"
              placeholder="Поиск по ID или ФИО…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <label className="cs-filter">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
              />
              <span>Только непрочитанные</span>
            </label>
          </div>
          <div className="cs-list">
            {chatsLoading && !visibleChats.length ? (
              <div className="cs-list__loading">Загрузка…</div>
            ) : visibleChats.length ? (
              <>
                {visibleChats.map(renderChatItem)}
                {!searchResults && !unreadOnly && chatsHasMore ? (
                  <button
                    type="button"
                    className="cs-load-more"
                    disabled={chatsLoadingMore}
                    onClick={() => void loadMoreChats()}
                  >
                    {chatsLoadingMore ? "Загрузка…" : "Загрузить ещё"}
                  </button>
                ) : null}
              </>
            ) : (
              <div className="cs-list__empty">
                {searchResults
                  ? "Ничего не найдено"
                  : unreadOnly
                    ? "Нет непрочитанных чатов"
                    : "Нет чатов"}
              </div>
            )}
          </div>
        </aside>

        <section className="cs-main">
          {!activeId ? (
            <div className="cs-empty">
              <div className="cs-empty__icon">💬</div>
              <div>Выберите чат, чтобы открыть переписку</div>
            </div>
          ) : (
            <>
              <div className="cs-head">
                <button type="button" className="cs-head__back" onClick={backToList} aria-label="Назад">
                  ←
                </button>
                <div className="cs-head__info">
                  <div className="cs-head__name">{activeChat?.fullname || `Абонент #${activeId}`}</div>
                  <div className="cs-head__meta">
                    <span className="cs-head__status">
                      <span className={`cs-chat__dot${activeChat?.is_online ? " is-online" : ""}`} />
                      {activeChat?.is_online ? "Онлайн" : "Оффлайн"}
                    </span>
                    {activeChat?.station_name ? ` · ${activeChat.station_name}` : ""}
                    {` · ID ${activeId}`}
                  </div>
                </div>
                <Link to={`/users/${activeId}`} className="cs-head__profile">
                  Карточка абонента →
                </Link>
              </div>

              <div className="cs-chat-viewport">
                <div className="cs-scroll" ref={scrollRef}>
                  <div className="cs-feed">
                    <div ref={topSentinelRef} style={{ height: 1 }} aria-hidden />
                    {loadingOlder ? <div className="cs-load-hint">Загрузка истории…</div> : null}
                    {msgLoading ? (
                      <div className="cs-load-hint">Загрузка сообщений…</div>
                    ) : messages.length ? (
                      messages.map(renderMessage)
                    ) : (
                      <div className="cs-feed-empty">Сообщений пока нет</div>
                    )}
                  </div>
                </div>
                <TicketChatScrollDown
                  visible={!atBottom}
                  pendingCount={pendingNewCount}
                  onClick={() => goToChatBottom()}
                  className="cs-scroll-down"
                  badgeClassName="cs-scroll-down__badge"
                />
              </div>

              <div className="cs-composer">
                {editing ? (
                  <div className="cs-reply-strip cs-reply-strip--edit">
                    <div className="cs-reply-strip__body">
                      <div className="cs-reply-strip__author">Редактирование сообщения</div>
                      <div className="cs-reply-strip__text">{plainPreview(editing.text)}</div>
                    </div>
                    <button
                      type="button"
                      className="cs-reply-strip__close"
                      onClick={() => {
                        setEditing(null);
                        setInput("");
                      }}
                    >
                      ×
                    </button>
                  </div>
                ) : replyTo ? (
                  <div className="cs-reply-strip">
                    <div className="cs-reply-strip__body">
                      <div className="cs-reply-strip__author">Ответ · {replyTo.whose_message}</div>
                      <div className="cs-reply-strip__text">{plainPreview(replyTo.text)}</div>
                    </div>
                    <button type="button" className="cs-reply-strip__close" onClick={() => setReplyTo(null)}>
                      ×
                    </button>
                  </div>
                ) : null}
                {file && !editing ? (
                  <div className="cs-file-chip cs-file-chip--img">
                    {filePreviewUrl ? (
                      <img src={filePreviewUrl} alt="" className="cs-file-chip__thumb" />
                    ) : null}
                    <span className="cs-file-chip__name">{truncateFilename(file.name)}</span>
                    <span className="cs-file-chip__meta">{formatBytes(file.size)}</span>
                    <button type="button" className="cs-file-chip__rm" onClick={clearAttachedFile}>
                      ×
                    </button>
                  </div>
                ) : null}
                <div className="cs-crow">
                  {!editing ? (
                    <label className="cs-attach" title="Прикрепить изображение">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                        <path
                          d="M14 8l-4.2 4.2a3 3 0 104.2 4.2l5-5a4 4 0 00-5.7-5.7l-5.8 5.8"
                          stroke="currentColor"
                          strokeWidth="1.7"
                          strokeLinecap="round"
                        />
                      </svg>
                      <input
                        type="file"
                        hidden
                        accept="image/jpeg,image/png,image/gif,image/webp,image/bmp,image/*"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) attachImage(f);
                          e.currentTarget.value = "";
                        }}
                      />
                    </label>
                  ) : null}
                  <textarea
                    className="cs-input"
                    rows={1}
                    placeholder={
                      editing
                        ? "Изменить сообщение… Ctrl + Enter — сохранить"
                        : file
                          ? "Текст недоступен при прикреплённом изображении"
                          : "Сообщение абоненту… Ctrl + Enter — отправить"
                    }
                    value={input}
                    disabled={sending || Boolean(file && !editing)}
                    onChange={(e) => {
                      const next = e.target.value;
                      if (next.trim() && file) clearAttachedFile();
                      setInput(next);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Escape" && editing) {
                        e.preventDefault();
                        setEditing(null);
                        setInput("");
                        return;
                      }
                      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        void handleSend();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="cs-send"
                    disabled={sending || (editing ? !input.trim() : (!input.trim() && !file) || (Boolean(input.trim()) && Boolean(file)))}
                    onClick={() => void handleSend()}
                    title={editing ? "Сохранить" : "Отправить"}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                      <path
                        d="M12 19V6M12 6l-5 5M12 6l5 5"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </div>

      {contextMenu ? (
        <ChatMessageContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          own={contextMenu.msg.answer && contextMenu.msg.user_id === viewerId}
          onAction={(action) => handleMenuAction(action, contextMenu.msg)}
          onClose={() => setContextMenu(null)}
        />
      ) : null}

      {lightbox ? (
        <div className="cs-imgv" role="dialog" aria-modal="true" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="Просмотр" onClick={(e) => e.stopPropagation()} />
        </div>
      ) : null}
    </div>
  );
}
