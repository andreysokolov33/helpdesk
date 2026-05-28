import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import MessageBody from "@/components/MessageBody";
import TicketDeleteMessageModal from "@/components/TicketDeleteMessageModal";
import TicketDeliveryTicks from "@/components/TicketDeliveryTicks";
import TicketMessageContextMenu, { type MessageMenuAction } from "@/components/TicketMessageContextMenu";
import TicketChatScrollDown from "@/components/TicketChatScrollDown";
import TicketMessageReplyQuote from "@/components/TicketMessageReplyQuote";
import { postDisconnect, type FastCheckResponse } from "@/api/userProfile";
import TicketClassifyModal, { type ClassifyAction } from "@/workspace/TicketClassifyModal";
import TicketFastCheckDrawer from "@/workspace/TicketFastCheckDrawer";
import { formatWorkDurationSince } from "@/utils/ticketFormat";
import {
  priorityBadgeClass,
  sourceBadgeClass,
  ticketSupportLineBadgeClass,
  ticketSupportLineShortLabel,
} from "@/utils/ticketLabels";
import {
  fetchTicketDetail,
  fetchTicketMessages,
  formatMsgTime,
  formatTicketCreated,
  deleteTicketMessage,
  normalizeReadReceipts,
  sendTicketMessage,
  updateTicketMessage,
  type TicketDetail,
  type TicketMessage,
} from "@/api/ticket";
import {
  applyReadReceiptsToMessages,
  canMessageContextMenu,
  mergeReadReceipts,
  mergeTicketMessages,
  ticketAuthorLabel,
  ticketAvatarLetter,
  ticketBblClass,
  ticketMavClass,
  ticketMsgRowClass,
} from "@/utils/ticketMessages";
import {
  CHAT_PAGE_SIZE,
  CHAT_SCROLL_EDGE_PX,
  isChatAtBottom,
  isChatNearBottom,
  isChatNearTop,
  maxLoadedMessageId,
  minLoadedMessageId,
  preserveScrollOnPrepend,
  scrollChatToBottom,
} from "@/utils/ticketChatScroll";

const MSG_POLL_MS = 5000;

type AttachBlockProps = { msg: TicketMessage };

function AttachmentsBlock({ msg }: AttachBlockProps) {
  const items = [
    ...(msg.legacy_file_url
      ? [
          {
            id: -1,
            file_path: msg.legacy_file_url,
            original_filename: "Файл",
            is_image: /\.(jpe?g|png|gif|webp|bmp)$/i.test(msg.legacy_file_url),
          },
        ]
      : []),
    ...msg.attachments,
  ];
  if (!items.length) return null;
  return (
    <div className="tk-att">
      {items.map((a) =>
        a.is_image ? (
          <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-img">
            <img src={a.file_path} alt={a.original_filename || "Вложение"} loading="lazy" />
          </a>
        ) : (
          <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-file">
            {a.original_filename || "Скачать файл"}
          </a>
        ),
      )}
    </div>
  );
}

export default function TicketPage() {
  const { ticketId: ticketIdParam } = useParams();
  const ticketId = Number(ticketIdParam);
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesRef = useRef<TicketMessage[]>([]);
  const readReceiptsRef = useRef<Record<number, string>>({});
  const atBottomRef = useRef(true);
  const loadingOlderRef = useRef(false);
  const loadingNewerRef = useRef(false);
  const didInitialAutoscrollRef = useRef(false);

  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [hasOlder, setHasOlder] = useState(false);
  const [hasNewer, setHasNewer] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [loadingNewer, setLoadingNewer] = useState(false);
  const [atBottom, setAtBottom] = useState(true);
  const [pendingNewCount, setPendingNewCount] = useState(0);
  const [highlightId, setHighlightId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sending, setSending] = useState(false);
  const [sideOpen, setSideOpen] = useState(true);
  const [classifyOpen, setClassifyOpen] = useState(false);
  const [classifyAction, setClassifyAction] = useState<ClassifyAction>("close");
  const [nowPulse, setNowPulse] = useState(() => Date.now());
  const [checkOpen, setCheckOpen] = useState(false);
  const [checkCache, setCheckCache] = useState<FastCheckResponse | null>(null);
  const [checkLoading, setCheckLoading] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; msg: TicketMessage } | null>(null);
  const [replyTo, setReplyTo] = useState<TicketMessage | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<TicketMessage | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setContextMenu(null);
    setReplyTo(null);
    setEditingId(null);
    setDeleteTarget(null);
    setHasOlder(false);
    setHasNewer(false);
    setPendingNewCount(0);
    setAtBottom(true);
    atBottomRef.current = true;
    didInitialAutoscrollRef.current = false;
  }, [ticketId]);

  const load = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) {
      setError("Некорректный ID тикета");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [d, m] = await Promise.all([
        fetchTicketDetail(ticketId),
        fetchTicketMessages(ticketId, { limit: CHAT_PAGE_SIZE }),
      ]);
      const receipts = normalizeReadReceipts(m.read_receipts);
      readReceiptsRef.current = receipts;
      setDetail(d);
      setMessages(applyReadReceiptsToMessages(m.messages, receipts));
      setHasOlder(Boolean(m.has_older));
      setHasNewer(Boolean(m.has_newer));
      setPendingNewCount(0);
      atBottomRef.current = true;
      setAtBottom(true);
      requestAnimationFrame(() => {
        const el = scrollRef.current;
        if (el) scrollChatToBottom(el);
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
      setDetail(null);
      setMessages([]);
      setHasOlder(false);
      setHasNewer(false);
      readReceiptsRef.current = {};
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  useLayoutEffect(() => {
    if (didInitialAutoscrollRef.current) return;
    if (loading || error || !detail) return;
    const el = scrollRef.current;
    if (!el) return;
    scrollChatToBottom(el);
    didInitialAutoscrollRef.current = true;
    atBottomRef.current = true;
    setAtBottom(true);
    setPendingNewCount(0);
  }, [loading, error, detail, messages.length]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const pollMessages = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) return;
    const sinceId = maxLoadedMessageId(messagesRef.current);
    try {
      const res = await fetchTicketMessages(ticketId, { sinceId });
      const incomingReceipts = normalizeReadReceipts(res.read_receipts);
      const receipts = mergeReadReceipts(readReceiptsRef.current, incomingReceipts);
      const hasNew = res.messages.length > 0;
      const hasReceiptUpdates = Object.keys(incomingReceipts).length > 0;
      if (!hasNew && !hasReceiptUpdates) return;
      readReceiptsRef.current = receipts;
      setMessages((prev) =>
        applyReadReceiptsToMessages(hasNew ? mergeTicketMessages(prev, res.messages) : prev, receipts),
      );
      if (atBottomRef.current && hasNew) {
        setHasNewer(false);
      }
      if (atBottomRef.current) {
        if (hasNew) {
          requestAnimationFrame(() => {
            const el = scrollRef.current;
            if (el) scrollChatToBottom(el);
          });
        }
        setPendingNewCount(0);
      } else if (hasNew) {
        setPendingNewCount((c) => c + res.messages.length);
      }
    } catch {
      /* поллинг не мешает работе чата */
    }
  }, [ticketId]);

  const loadOlderMessages = useCallback(async () => {
    if (!hasOlder || loadingOlderRef.current) return;
    const minId = minLoadedMessageId(messagesRef.current);
    if (minId == null) return;
    const el = scrollRef.current;
    if (!el) return;
    loadingOlderRef.current = true;
    setLoadingOlder(true);
    const prevHeight = el.scrollHeight;
    const prevTop = el.scrollTop;
    try {
      const res = await fetchTicketMessages(ticketId, { beforeId: minId, limit: CHAT_PAGE_SIZE });
      const receipts = mergeReadReceipts(
        readReceiptsRef.current,
        normalizeReadReceipts(res.read_receipts),
      );
      readReceiptsRef.current = receipts;
      setHasOlder(Boolean(res.has_older));
      setMessages((prev) =>
        applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts),
      );
      requestAnimationFrame(() => {
        const box = scrollRef.current;
        if (box) preserveScrollOnPrepend(box, prevHeight, prevTop);
      });
    } catch {
      /* тихо */
    } finally {
      loadingOlderRef.current = false;
      setLoadingOlder(false);
    }
  }, [ticketId, hasOlder]);

  useEffect(() => {
    const root = scrollRef.current;
    const target = topSentinelRef.current;
    if (!root || !target) return;
    if (loading || error || !detail) return;
    if (!didInitialAutoscrollRef.current) return;

    const obs = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        void loadOlderMessages();
      },
      {
        root,
        rootMargin: `${CHAT_SCROLL_EDGE_PX}px 0px 0px 0px`,
        threshold: 0,
      },
    );
    obs.observe(target);
    return () => obs.disconnect();
  }, [loading, error, detail, loadOlderMessages]);

  const loadNewerMessages = useCallback(async () => {
    if (!hasNewer || loadingNewerRef.current) return;
    const maxId = maxLoadedMessageId(messagesRef.current);
    if (maxId <= 0) return;
    loadingNewerRef.current = true;
    setLoadingNewer(true);
    try {
      const res = await fetchTicketMessages(ticketId, { afterId: maxId, limit: CHAT_PAGE_SIZE });
      const receipts = mergeReadReceipts(
        readReceiptsRef.current,
        normalizeReadReceipts(res.read_receipts),
      );
      readReceiptsRef.current = receipts;
      setHasNewer(Boolean(res.has_newer));
      setMessages((prev) =>
        applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts),
      );
    } catch {
      /* тихо */
    } finally {
      loadingNewerRef.current = false;
      setLoadingNewer(false);
    }
  }, [ticketId, hasNewer]);

  const goToChatBottom = useCallback(async () => {
    setPendingNewCount(0);
    let more = true;
    let guard = 0;
    while (more && guard < 12) {
      const maxId = maxLoadedMessageId(messagesRef.current);
      if (maxId <= 0) break;
      try {
        const res = await fetchTicketMessages(ticketId, { afterId: maxId, limit: CHAT_PAGE_SIZE });
        const receipts = mergeReadReceipts(
          readReceiptsRef.current,
          normalizeReadReceipts(res.read_receipts),
        );
        readReceiptsRef.current = receipts;
        more = Boolean(res.has_newer);
        setHasNewer(more);
        if (res.messages.length) {
          setMessages((prev) =>
            applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts),
          );
        } else {
          more = false;
        }
      } catch {
        more = false;
      }
      guard += 1;
    }
    atBottomRef.current = true;
    setAtBottom(true);
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) scrollChatToBottom(el);
    });
  }, [ticketId]);

  const flashMessage = useCallback((id: number) => {
    setHighlightId(id);
    window.setTimeout(() => setHighlightId((cur) => (cur === id ? null : cur)), 2000);
  }, []);

  const scrollToMessage = useCallback(
    async (id: number) => {
      if (id <= 0) return;
      const existing = scrollRef.current?.querySelector(`[data-msg-id="${id}"]`);
      if (existing) {
        existing.scrollIntoView({ behavior: "smooth", block: "center" });
        flashMessage(id);
        return;
      }
      try {
        const res = await fetchTicketMessages(ticketId, { aroundId: id, limit: CHAT_PAGE_SIZE });
        const receipts = mergeReadReceipts(
          readReceiptsRef.current,
          normalizeReadReceipts(res.read_receipts),
        );
        readReceiptsRef.current = receipts;
        setHasOlder(Boolean(res.has_older));
        setHasNewer(Boolean(res.has_newer));
        setMessages((prev) =>
          applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts),
        );
        setPendingNewCount(0);
        atBottomRef.current = false;
        setAtBottom(false);
        requestAnimationFrame(() => {
          const el = scrollRef.current?.querySelector(`[data-msg-id="${id}"]`);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            flashMessage(id);
          }
        });
      } catch (e: unknown) {
        window.alert(e instanceof Error ? e.message : "Не удалось перейти к сообщению");
      }
    },
    [ticketId, flashMessage],
  );

  useEffect(() => {
    if (loading || error || !detail) return;
    const id = window.setInterval(() => void pollMessages(), MSG_POLL_MS);
    return () => window.clearInterval(id);
  }, [loading, error, detail, pollMessages]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const bottom = isChatAtBottom(el, CHAT_SCROLL_EDGE_PX);
      atBottomRef.current = bottom;
      setAtBottom(bottom);
      if (bottom) setPendingNewCount(0);
      if (!bottom && isChatNearBottom(el, CHAT_SCROLL_EDGE_PX) && hasNewer) void loadNewerMessages();
    };
    onScroll();
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [loading, detail?.id, loadOlderMessages, loadNewerMessages, hasNewer]);

  useEffect(() => {
    const id = window.setInterval(() => setNowPulse(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const ta = inputRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  function openClassify(action: ClassifyAction) {
    setClassifyAction(action);
    setClassifyOpen(true);
  }

  function openCheck() {
    if (!detail?.user_id) {
      window.alert("Абонент не определён — проверка недоступна");
      return;
    }
    setCheckOpen(true);
  }

  function clearComposerMode() {
    setReplyTo(null);
    setEditingId(null);
  }

  function focusComposer() {
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function handleMessageMenuAction(action: MessageMenuAction, msg: TicketMessage) {
    setContextMenu(null);
    if (action === "copy") {
      const text = msg.text?.trim() || "";
      if (!text) return;
      void navigator.clipboard.writeText(text).catch(() => {
        window.alert("Не удалось скопировать текст");
      });
      return;
    }
    if (action === "reply") {
      setEditingId(null);
      setReplyTo(msg);
      setFile(null);
      focusComposer();
      return;
    }
    if (action === "edit") {
      setReplyTo(null);
      setEditingId(msg.id);
      setInput(msg.text || "");
      setFile(null);
      focusComposer();
      return;
    }
    if (action === "delete") {
      setDeleteTarget(msg);
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteTicketMessage(ticketId, deleteTarget.id);
      setMessages((prev) => prev.filter((m) => m.id !== deleteTarget.id));
      if (replyTo?.id === deleteTarget.id) setReplyTo(null);
      if (editingId === deleteTarget.id) {
        setEditingId(null);
        setInput("");
      }
      setDeleteTarget(null);
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : "Не удалось удалить");
    } finally {
      setDeleting(false);
    }
  }

  async function submit() {
    const t = input.trim();
    if (!t && !file && !editingId) return;
    if (!detail?.can_reply && detail?.chat_mode === "mail") return;
    if (editingId && !t) return;
    setSending(true);
    try {
      if (editingId) {
        const updated = await updateTicketMessage(ticketId, editingId, t);
        setMessages((prev) =>
          prev.map((m) => (m.id === editingId ? { ...m, ...updated } : m)),
        );
        setEditingId(null);
        setInput("");
        setFile(null);
      } else {
        const msg = await sendTicketMessage(ticketId, t, file, replyTo?.id ?? null);
        setMessages((prev) =>
          applyReadReceiptsToMessages(mergeTicketMessages(prev, [msg]), readReceiptsRef.current),
        );
        atBottomRef.current = true;
        setAtBottom(true);
        setPendingNewCount(0);
        setHasNewer(false);
        setInput("");
        setFile(null);
        setReplyTo(null);
        requestAnimationFrame(() => {
          const el = scrollRef.current;
          if (el) scrollChatToBottom(el);
        });
      }
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : editingId ? "Не удалось сохранить" : "Не удалось отправить");
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <div className="tp on">
        <div className="pg">
          <p className="ch-list-loading">Загрузка тикета…</p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="tp on">
        <div className="pg">
          <div className="ch-list-err">{error || "Тикет не найден"}</div>
          <Link to="/chats" className="tk-back-link">
            ← К чатам
          </Link>
        </div>
      </div>
    );
  }

  const subName =
    detail.subscriber_display_name || detail.subscriber_name || detail.caller_name || "Абонент";
  const introBody = detail.body?.trim() || "";
  const chatMessages = messages.filter((m) => !m.is_initial);
  const hasIntro = introBody.length > 0;
  const online = Boolean(detail.user_id) ? Boolean(detail.subscriber_online) : false;

  return (
    <div className="tp on" id="tp-ticket" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden", position: "relative" }}>
        <div className="tbar">
          <button type="button" className="tbk" onClick={() => navigate("/chats")}>
            ← Назад
          </button>
          <div style={{ width: 1, height: 16, background: "var(--ln)" }} />
          <div className="tk-tbar-head">
            <span className="tk-tbar-id">#{detail.id}</span>
            <span className="tk-tbar-sep" aria-hidden>
              ·
            </span>
            <h1 className="tk-tbar-title">{detail.title}</h1>
            <span className={`ch-status ch-status--${detail.status}`}>{detail.status_label}</span>
          </div>
          <div className="tacts">
            <button
              type="button"
              className={`diag-btn${checkLoading ? " running" : ""}`}
              onClick={openCheck}
              title={detail.user_id ? "Быстрая проверка абонента" : "Укажите абонента в тикете"}
            >
              <svg width="13" height="13" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M2 15h3l2-5 3 8 2-10 2 4h4" />
                <circle cx="17" cy="12" r="1.5" fill="currentColor" stroke="none" />
              </svg>
              {checkLoading ? "Проверяю…" : "Проверка"}
            </button>
            <button type="button" className="tb3" onClick={() => openClassify("esc")}>
              Инженерам
            </button>
            <button type="button" className="tb3 cls" onClick={() => openClassify("close")}>
              Завершить
            </button>
            <button
              type="button"
              className={`tb3 tk-panel-toggle${sideOpen ? " on" : ""}`}
              onClick={() => setSideOpen((v) => !v)}
              title={sideOpen ? "Скрыть панель абонента" : "Показать панель абонента"}
            >
              {sideOpen ? "Панель ▶" : "◀ Панель"}
            </button>
          </div>
        </div>

        <div className="tbody tk-ticket-body">
          {detail.user_id != null ? (
            <TicketFastCheckDrawer
              userId={detail.user_id}
              open={checkOpen}
              subscriberSidebarOpen={sideOpen}
              cachedData={checkCache}
              onCachedData={setCheckCache}
              onClose={() => setCheckOpen(false)}
              onLoadingChange={setCheckLoading}
              onDisconnect={() =>
                postDisconnect(detail.user_id!).then(() => {
                  void load();
                })
              }
            />
          ) : null}
          <div className="czone tk-chat-main">
            <div className="tk-chat-viewport">
              <div className="cscrl tk-chat-scroll" ref={scrollRef}>
                <div className="tk-chat-feed">
                <div ref={topSentinelRef} style={{ height: 1 }} aria-hidden />
                {loadingOlder ? (
                  <div className="tk-chat-load-hint" aria-live="polite">
                    Загрузка предыдущих сообщений…
                  </div>
                ) : null}
                {hasIntro ? (
                  <div className="tk-intro" role="note">
                    <div className="tk-intro__eyebrow">Суть обращения</div>
                    <MessageBody text={introBody} className="tk-intro__text" />
                    {detail.date_of_create_iso ? (
                      <div className="tk-intro__meta">{formatMsgTime(detail.date_of_create_iso)}</div>
                    ) : null}
                  </div>
                ) : null}

                {chatMessages.length > 0 && hasIntro ? (
                  <div className="tk-chat-divider" aria-hidden>
                    <span>Переписка</span>
                  </div>
                ) : null}

                {chatMessages.length === 0 && !hasIntro ? (
                  <div className="tk-chat-empty">Сообщений пока нет</div>
                ) : (
                  chatMessages.map((m) =>
                    m.side === "bot" ? (
                      <div key={m.id} className="msg bot">
                        <div className="mc2">
                          <div className="bbl bot">
                            <div className="tk-msg-label">{ticketAuthorLabel(m, subName)}</div>
                            <MessageBody text={m.text} />
                            <AttachmentsBlock msg={m} />
                          </div>
                          <div className="mtm">{formatMsgTime(m.created_at_iso) || "—"}</div>
                        </div>
                      </div>
                    ) : (
                      <div
                        key={m.id}
                        data-msg-id={m.id}
                        className={`${ticketMsgRowClass(m.side)}${highlightId === m.id ? " tk-msg--highlight" : ""}`}
                        onContextMenu={(e) => {
                          if (!canMessageContextMenu(m.side, m.id)) return;
                          e.preventDefault();
                          setContextMenu({ x: e.clientX, y: e.clientY, msg: m });
                        }}
                      >
                        <div className={ticketMavClass(m.side)}>{ticketAvatarLetter(m, subName)}</div>
                        <div className="mc2">
                          <div className={ticketBblClass(m.side)}>
                            <div className="tk-msg-label">{ticketAuthorLabel(m, subName)}</div>
                            {m.reply_preview ? (
                              <TicketMessageReplyQuote preview={m.reply_preview} onJump={scrollToMessage} />
                            ) : null}
                            <MessageBody text={m.text} />
                            <AttachmentsBlock msg={m} />
                          </div>
                          <div className="mtm">
                            <span>
                              {formatMsgTime(m.created_at_iso) || "—"}
                              {m.is_edited ? (
                                <span className="tk-msg-edited" title={m.updated_at_iso || undefined}>
                                  {" "}
                                  · изменено
                                  {m.updated_at_iso ? ` ${formatMsgTime(m.updated_at_iso)}` : ""}
                                </span>
                              ) : null}
                            </span>
                            <TicketDeliveryTicks
                              side={m.side}
                              recipientReadAtIso={m.recipient_read_at_iso}
                              ticketSource={detail.source}
                            />
                          </div>
                        </div>
                      </div>
                    ),
                  )
                )}
                {loadingNewer ? (
                  <div className="tk-chat-load-hint tk-chat-load-hint--bottom" aria-live="polite">
                    Загрузка…
                  </div>
                ) : null}
              </div>
            </div>
              <TicketChatScrollDown
                visible={!atBottom}
                pendingCount={pendingNewCount}
                onClick={() => void goToChatBottom()}
              />
            </div>

            <div className="tk-composer">
              {!detail.can_reply ? (
                <div className="tk-no-reply">
                  Абонент не определён — ответ в чат недоступен. Укажите абонента в карточке или завершите
                  обработку звонка.
                </div>
              ) : (
                <>
                  {replyTo ? (
                    <div className="tk-composer-mode">
                      <div className="tk-composer-mode__label">Ответ на сообщение</div>
                      <TicketMessageReplyQuote
                        preview={
                          replyTo.reply_preview ?? {
                            id: replyTo.id,
                            author_name: ticketAuthorLabel(replyTo, subName),
                            text: replyTo.text.slice(0, 100),
                          }
                        }
                        onJump={scrollToMessage}
                      />
                      <button
                        type="button"
                        className="tk-composer-mode__close"
                        onClick={() => setReplyTo(null)}
                        aria-label="Отменить ответ"
                      >
                        ×
                      </button>
                    </div>
                  ) : null}
                  {editingId ? (
                    <div className="tk-composer-mode tk-composer-mode--edit">
                      <span className="tk-composer-mode__label">Редактирование сообщения</span>
                      <button
                        type="button"
                        className="tk-composer-mode__close"
                        onClick={() => {
                          setEditingId(null);
                          setInput("");
                        }}
                        aria-label="Отменить редактирование"
                      >
                        ×
                      </button>
                    </div>
                  ) : null}
                  <div className="tk-composer__box">
                    <textarea
                      ref={inputRef}
                      className="tk-composer__input"
                      rows={1}
                      placeholder={
                        editingId ? "Измените текст сообщения…" : replyTo ? "Ваш ответ…" : "Ответ клиенту…"
                      }
                      value={input}
                      disabled={sending}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          if (editingId || replyTo) {
                            e.preventDefault();
                            clearComposerMode();
                            setInput("");
                          }
                          return;
                        }
                        if (e.ctrlKey && e.key === "Enter") {
                          e.preventDefault();
                          submit();
                        }
                      }}
                    />
                    <div className="tk-composer__actions">
                      <label
                        className={`tk-composer__attach${editingId ? " tk-composer__attach--disabled" : ""}`}
                        title={editingId ? "При редактировании вложения недоступны" : "Прикрепить файл"}
                      >
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
                          disabled={Boolean(editingId)}
                          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
                          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        />
                      </label>
                      <button
                        type="button"
                        className="tk-composer__send"
                        disabled={sending || (!input.trim() && !file && !editingId)}
                        onClick={submit}
                        title={editingId ? "Сохранить" : "Отправить"}
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
                  {file ? (
                    <div className="tk-composer__file">
                      <span className="tk-composer__file-name">{file.name}</span>
                      <button type="button" className="tk-file-clear" onClick={() => setFile(null)}>
                        Убрать
                      </button>
                    </div>
                  ) : null}
                  <div className="tk-composer__hint">
                    {editingId ? "Ctrl+Enter — сохранить · Esc — отмена" : "Ctrl+Enter — отправить · Esc — отмена ответа"}
                  </div>
                </>
              )}
            </div>
          </div>

          {contextMenu ? (
            <TicketMessageContextMenu
              x={contextMenu.x}
              y={contextMenu.y}
              message={contextMenu.msg}
              onAction={handleMessageMenuAction}
              onClose={() => setContextMenu(null)}
            />
          ) : null}

          <TicketDeleteMessageModal
            open={Boolean(deleteTarget)}
            busy={deleting}
            onClose={() => {
              if (!deleting) setDeleteTarget(null);
            }}
            onConfirm={() => void confirmDelete()}
          />

          <aside className={`tk-sidebar ip${sideOpen ? "" : " closed"}`} aria-label="Информация о тикете">
            <div className="tk-sidebar__accent" aria-hidden />
            <div className="ips">
              <div className="ipb">
                <div className="ipl">Абонент</div>
                <div
                  className={detail.subscriber_is_juridical === 2 ? "tk-side-name tk-side-name--jur" : "tk-side-name"}
                >
                  <span
                    aria-hidden
                    style={{
                      display: "inline-block",
                      width: 8,
                      height: 8,
                      borderRadius: 999,
                      background: online ? "var(--ok)" : "var(--lm)",
                      marginRight: 8,
                      verticalAlign: "middle",
                      boxShadow: online ? "0 0 0 2px rgba(27,122,72,.14)" : "none",
                    }}
                  />
                  {subName}
                </div>
                {detail.caller_name && detail.user_id == null ? (
                  <div className="tk-side-meta">Как представился: {detail.caller_name}</div>
                ) : null}
                {detail.user_id != null ? <div className="tk-side-meta">ID: {detail.user_id}</div> : null}
                {detail.subscriber_login ? (
                  <div className="tk-side-meta">Логин: {detail.subscriber_login}</div>
                ) : null}
                {detail.subscriber_profile_user_id != null ? (
                  <Link to={`/users/${detail.subscriber_profile_user_id}`} className="tk-profile-link">
                    Карточка абонента →
                  </Link>
                ) : null}
              </div>

              <div className="ipb">
                <div className="ipl">Тикет</div>
                <div className="kv">
                  <span className="kvk">Источник</span>
                  <span className="kvv">
                    <span className={`ch-source ch-source--${sourceBadgeClass(detail.source)}`}>
                      {detail.source_label}
                    </span>
                  </span>
                </div>
                <div className="kv">
                  <span className="kvk">Линия</span>
                  <span className="kvv">
                    <span
                      className={`ch-line ch-line--${ticketSupportLineBadgeClass(detail.support_line)}`}
                    >
                      {ticketSupportLineShortLabel(detail.support_line)}
                    </span>
                  </span>
                </div>
                {detail.category_label ? (
                  <div className="kv">
                    <span className="kvk">Категория</span>
                    <span className="kvv">{detail.category_label}</span>
                  </div>
                ) : null}
                <div className="kv">
                  <span className="kvk">Приоритет</span>
                  <span className="kvv">
                    <span
                      className={`ch-priority ch-priority--${priorityBadgeClass(detail.priority)}`}
                      title={detail.priority_label ?? "Средний"}
                    >
                      {detail.priority_label ?? "Средний"}
                    </span>
                  </span>
                </div>
                {detail.station_name ? (
                  <div className="kv">
                    <span className="kvk">Станция</span>
                    <span className="kvv">{detail.station_name}</span>
                  </div>
                ) : null}
                {detail.assignee_name ? (
                  <div className="kv">
                    <span className="kvk">Исполнитель</span>
                    <span className="kvv">{detail.assignee_name}</span>
                  </div>
                ) : null}
                <div className="kv">
                  <span className="kvk">Создан</span>
                  <span className="kvv">{formatTicketCreated(detail.date_of_create_iso) || "—"}</span>
                </div>
                {detail.date_of_create_iso ? (
                  <div className="kv">
                    <span className="kvk">Время в работе</span>
                    <span className="kvv">{formatWorkDurationSince(detail.date_of_create_iso, nowPulse)}</span>
                  </div>
                ) : null}
              </div>
            </div>
          </aside>
        </div>
      </div>

      <TicketClassifyModal
        open={classifyOpen}
        ticketId={detail.id}
        ticketSource={detail.source}
        initialCategoryId={detail.category_id}
        initialCategoryParentId={detail.category_parent_id}
        action={classifyAction}
        onClose={() => setClassifyOpen(false)}
        onConfirm={() => setClassifyOpen(false)}
      />
    </div>
  );
}
