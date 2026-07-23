import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import RichEditor, { type RichEditorHandle } from "@/components/RichEditor";
import { Link, useParams } from "react-router-dom";
import MessageBody from "@/components/MessageBody";
import TicketCrossTicketMessageModal from "@/components/TicketCrossTicketMessageModal";
import TicketDeleteMessageModal from "@/components/TicketDeleteMessageModal";
import TicketDeliveryTicks from "@/components/TicketDeliveryTicks";
import TicketMessageContextMenu, { type MessageMenuAction } from "@/components/TicketMessageContextMenu";
import TicketChatScrollDown from "@/components/TicketChatScrollDown";
import TicketMessageReplyQuote from "@/components/TicketMessageReplyQuote";
import { postDisconnect, type FastCheckResponse } from "@/api/userProfile";
import { isLkTicketSource } from "@/utils/ticketLabels";
import {
  fetchTicketDetail,
  fetchTicketMessages,
  fetchMessageContext,
  fetchTicketReadReceipts,
  formatMsgTime,
  mergeTicketPollSnapshot,
  ticketPollSnapshotChanged,
  reopenTicket,
  type TicketPollSnapshot,
  deleteTicketMessage,
  sendTicketMessage,
  takeTicketBackToKs,
  transferTicketToEngineers,
  updateTicketPriority,
  type TicketPriority,
  updateTicketMessage,
  uploadTicketAttachment,
  detachTicketAttachment,
  type TicketDetail,
  type TicketMessage,
  type TicketMessageReadBy,
  type TicketMessageReplyPreview,
  type TicketReadReceiptsResult,
} from "@/api/ticket";
import {
  applyReadReceiptsToMessages,
  canMessageContextMenu,
  mergeIncomingReadState,
  mergeTicketMessages,
  isEngineerTicketMessage,
  ticketAuthorLabel,
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
  watchChatScrollToBottom,
} from "@/utils/ticketChatScroll";
import { compressImageToWebp } from "@/utils/imageCompress";
import { formatBytes } from "@/utils/formatBytes";
import TicketMessageAttachments, { collectMessageImageUrls } from "@/components/TicketMessageAttachments";
import FileBadge, { truncateFilename } from "@/components/FileBadge";
import ToastNotice, { type ToastVariant } from "@/components/ToastNotice";
import TicketMacroBar, { type TicketChatPanelMode } from "@/components/TicketMacroBar";
import {
  commentToMessage,
  deleteTicketComment,
  fetchTicketComments,
  maxTicketCommentId,
  mergeTicketComments,
  minTicketCommentId,
  sendTicketComment,
  updateTicketComment,
  isOwnTicketComment,
  type TicketComment,
} from "@/api/ticketComments";
import TicketQueueSidebar from "@/components/TicketQueueSidebar";
import TicketHelperPanel from "@/components/TicketHelperPanel";
import TicketKbArticleOverlay from "@/components/TicketKbArticleOverlay";
import TicketLinkSubscriberModal from "@/workspace/TicketLinkSubscriberModal";
import { fetchUserProfile, type UserProfileResponse } from "@/api/userProfile";
import { macroTextToEditorHtml, type HelpdeskMacro } from "@/api/macros";
import { validateTicketMessage } from "@/utils/ticketMessageValidation";
import { useMediaQuery } from "@/utils/useMediaQuery";

const MSG_POLL_MS = 5000;
const READ_RECEIPTS_POLL_MS = 3000;

/** Безопасный id вложения (randomUUID недоступен в insecure HTTP). */
function newUploadId(): string {
  try {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
  } catch {
    /* insecure context */
  }
  return `up-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function TicketPage() {
  const { ticketId: ticketIdParam } = useParams();
  const ticketId = Number(ticketIdParam);
  const scrollRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<RichEditorHandle>(null);
  const messagesRef = useRef<TicketMessage[]>([]);
  const readReceiptsRef = useRef<Record<number, string>>({});
  const readByReceiptsRef = useRef<Record<number, TicketMessageReadBy[]>>({});
  const atBottomRef = useRef(true);
  const loadingOlderRef = useRef(false);
  const loadingNewerRef = useRef(false);
  const didInitialAutoscrollRef = useRef(false);
  const initialScrollCleanupRef = useRef<(() => void) | null>(null);
  const loadGenRef = useRef(0);
  const detailRef = useRef<TicketDetail | null>(null);

  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [hasOlder, setHasOlder] = useState(false);
  const [hasNewer, setHasNewer] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [loadingNewer, setLoadingNewer] = useState(false);
  const [atBottom, setAtBottom] = useState(true);
  const [pendingNewCount, setPendingNewCount] = useState(0);
  const [highlightId, setHighlightId] = useState<number | null>(null);
  const [crossTicketMessageId, setCrossTicketMessageId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editorEmpty, setEditorEmpty] = useState(true);
  const [sending, setSending] = useState(false);
  const [helperCollapsed, setHelperCollapsed] = useState(false);
  const [kbArticleSlug, setKbArticleSlug] = useState<string | null>(null);
  const [mobilePanel, setMobilePanel] = useState<null | "queue" | "info">(null);
  const isMobileLayout = useMediaQuery("(max-width: 900px)");
  const [subscriberProfile, setSubscriberProfile] = useState<UserProfileResponse | null>(null);
  const [takeBackLoading, setTakeBackLoading] = useState(false);
  const [transferLoading, setTransferLoading] = useState(false);
  const [reopenLoading, setReopenLoading] = useState(false);
  const [priorityLoading, setPriorityLoading] = useState(false);
  const [queueRefreshNonce, setQueueRefreshNonce] = useState(0);
  const [chatPanel, setChatPanel] = useState<TicketChatPanelMode>("subscriber");
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [commentsHasOlder, setCommentsHasOlder] = useState(false);
  const [commentsLoadingOlder, setCommentsLoadingOlder] = useState(false);
  const [commentDraft, setCommentDraft] = useState("");
  const [commentEditingId, setCommentEditingId] = useState<number | null>(null);
  const [commentDeleteTarget, setCommentDeleteTarget] = useState<TicketComment | null>(null);
  const commentsRef = useRef<TicketComment[]>([]);
  const commentsLoadingOlderRef = useRef(false);
  const commentInputRef = useRef<HTMLTextAreaElement>(null);
  const chatPanelRef = useRef<TicketChatPanelMode>("subscriber");
  const subscriberSeenMaxIdRef = useRef(0);
  const [subscriberChatUnread, setSubscriberChatUnread] = useState(0);
  const [linkSubscriberOpen, setLinkSubscriberOpen] = useState(false);
  const [nowPulse, setNowPulse] = useState(() => Date.now());
  const [checkCache, setCheckCache] = useState<FastCheckResponse | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; msg: TicketMessage } | null>(null);
  const [replyTo, setReplyTo] = useState<TicketMessage | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingAttachments, setEditingAttachments] = useState<TicketMessage["attachments"]>([]);
  const [detachPendingIds, setDetachPendingIds] = useState<Set<number>>(new Set());
  const [deleteTarget, setDeleteTarget] = useState<TicketMessage | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [uploads, setUploads] = useState<
    {
      id: string;
      file: File;
      previewUrl?: string;
      status: "pending" | "uploading" | "done" | "error";
      uploaded: number;
      total: number;
      token?: string;
      err?: string;
      isImage?: boolean;
    }[]
  >([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const uploadingXhrRef = useRef<XMLHttpRequest | null>(null);
  const uploadingIdRef = useRef<string | null>(null);
  const autoSendRef = useRef(false);
  const [imgViewerOpen, setImgViewerOpen] = useState(false);
  const [imgViewerIndex, setImgViewerIndex] = useState(0);
  const imgViewerUrlRef = useRef<string | null>(null);
  const [toast, setToast] = useState<{ message: string; variant: ToastVariant } | null>(null);

  const uploadSummary = useMemo(() => {
    const total = uploads.reduce((s, u) => s + (u.total || 0), 0);
    const uploaded = uploads.reduce((s, u) => s + (u.uploaded || 0), 0);
    const pending = uploads.filter((u) => u.status === "pending" || u.status === "uploading").length;
    const doneTokens = uploads.filter((u) => u.status === "done" && u.token).map((u) => u.token!) as string[];
    const hasReady = uploads.some((u) => u.status === "done" && Boolean(u.token));
    return { total, uploaded, pending, doneTokens, hasReady };
  }, [uploads]);

  const allImageUrls = useMemo(() => {
    const out: string[] = [];
    for (const m of messages) {
      if (m.legacy_file_url && /\.(jpe?g|png|gif|webp|bmp)$/i.test(m.legacy_file_url)) {
        out.push(m.legacy_file_url);
      }
      for (const a of m.attachments || []) {
        if (a?.is_image && a.file_path) out.push(a.file_path);
      }
    }
    // uniq keep order
    return out.filter((u, i) => out.indexOf(u) === i);
  }, [messages]);

  const openImageViewer = useCallback(
    (url: string) => {
      const idx = allImageUrls.indexOf(url);
      const safeIdx = idx >= 0 ? idx : 0;
      imgViewerUrlRef.current = url;
      setImgViewerIndex(safeIdx);
      setImgViewerOpen(true);
    },
    [allImageUrls],
  );

  useEffect(() => {
    if (!imgViewerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setImgViewerOpen(false);
        return;
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setImgViewerIndex((i) => {
          const newIdx = allImageUrls.length ? (i - 1 + allImageUrls.length) % allImageUrls.length : 0;
          imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
          return newIdx;
        });
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setImgViewerIndex((i) => {
          const newIdx = allImageUrls.length ? (i + 1) % allImageUrls.length : 0;
          imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
          return newIdx;
        });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [imgViewerOpen, allImageUrls]);

  // Keep viewer index stable when allImageUrls changes (e.g. older messages prepended)
  useEffect(() => {
    if (!imgViewerOpen || !imgViewerUrlRef.current) return;
    const newIdx = allImageUrls.indexOf(imgViewerUrlRef.current);
    if (newIdx >= 0) setImgViewerIndex(newIdx);
  }, [allImageUrls, imgViewerOpen]);

  useEffect(() => {
    setContextMenu(null);
    setReplyTo(null);
    setEditingId(null);
    setEditingAttachments([]);
    setDeleteTarget(null);
    setHasOlder(false);
    setHasNewer(false);
    setPendingNewCount(0);
    setAtBottom(true);
    atBottomRef.current = true;
    didInitialAutoscrollRef.current = false;
    initialScrollCleanupRef.current?.();
    initialScrollCleanupRef.current = null;
    setChatPanel("subscriber");
    setComments([]);
    setCommentsHasOlder(false);
    setCommentDraft("");
    setCommentEditingId(null);
    setCommentDeleteTarget(null);
    setSubscriberChatUnread(0);
    subscriberSeenMaxIdRef.current = 0;
    setCheckCache(null);
    setKbArticleSlug(null);
  }, [ticketId]);

  useEffect(() => {
    chatPanelRef.current = chatPanel;
  }, [chatPanel]);

  const load = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) {
      setError("Некорректный ID тикета");
      return;
    }
    const gen = ++loadGenRef.current;
    const isInitial = detailRef.current == null;
    setError(null);
    try {
      const [d, m] = await Promise.all([
        fetchTicketDetail(ticketId),
        fetchTicketMessages(ticketId, { limit: CHAT_PAGE_SIZE }),
      ]);
      if (gen !== loadGenRef.current) return;
      const { receipts, readBy } = mergeIncomingReadState({}, {}, m);
      readReceiptsRef.current = receipts;
      readByReceiptsRef.current = readBy;
      setDetail(d);
      setMessages(applyReadReceiptsToMessages(m.messages, receipts, readBy));
      setHasOlder(Boolean(m.has_older));
      setHasNewer(Boolean(m.has_newer));
      setPendingNewCount(0);
      atBottomRef.current = true;
      setAtBottom(true);
    } catch (e: unknown) {
      if (gen !== loadGenRef.current) return;
      const msg = e instanceof Error ? e.message : "Ошибка загрузки";
      if (isInitial) {
        setError(msg);
        setDetail(null);
        setMessages([]);
        setHasOlder(false);
        setHasNewer(false);
        readReceiptsRef.current = {};
        readByReceiptsRef.current = {};
      } else {
        setToast({ message: msg, variant: "error" });
      }
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const uid = detail?.user_id;
    if (!uid) {
      setSubscriberProfile(null);
      return;
    }
    let cancelled = false;
    void fetchUserProfile(uid, 1, 10, false)
      .then((profile) => {
        if (!cancelled) setSubscriberProfile(profile);
      })
      .catch(() => {
        if (!cancelled) setSubscriberProfile(null);
      });
    return () => {
      cancelled = true;
    };
  }, [detail?.user_id]);

  useEffect(() => {
    if (!detail || isLkTicketSource(detail.source)) return;
    if (chatPanel !== "subscriber") {
      setChatPanel("subscriber");
      setCommentEditingId(null);
      setCommentDraft("");
      setCommentDeleteTarget(null);
    }
  }, [detail, chatPanel]);

  useLayoutEffect(() => {
    if (didInitialAutoscrollRef.current) return;
    if (error || !detail || detail.id !== ticketId) return;
    const el = scrollRef.current;
    if (!el) return;

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
  }, [error, detail, ticketId, messages.length]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    commentsRef.current = comments;
  }, [comments]);

  const loadComments = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) return;
    try {
      const res = await fetchTicketComments(ticketId, { limit: CHAT_PAGE_SIZE });
      setComments(res.comments);
      setCommentsHasOlder(Boolean(res.has_older));
      requestAnimationFrame(() => {
        const el = scrollRef.current;
        if (el) scrollChatToBottom(el);
      });
    } catch {
      setComments([]);
      setCommentsHasOlder(false);
    }
  }, [ticketId]);

  useEffect(() => {
    detailRef.current = detail;
  }, [detail]);

  const bumpQueueRefresh = useCallback(() => {
    setQueueRefreshNonce((n) => n + 1);
  }, []);

  const activeTicketQueueSync = useMemo(() => {
    if (!detail) return null;
    let lastPreview: string | null | undefined;
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const m = messages[i];
      if (m.is_initial) continue;
      const raw = (m.text || "").trim();
      lastPreview = raw || null;
      break;
    }
    return {
      id: detail.id,
      status: detail.status,
      status_label: detail.status_label,
      queue_line: detail.queue_line,
      queue_line_label: detail.queue_line_label,
      action_by: detail.action_by,
      chat_turn: detail.chat_turn,
      action_since: detail.action_since_iso ?? null,
      list_highlight: detail.list_highlight ?? "none",
      communication_state: detail.communication_state ?? null,
      communication_label: detail.communication_label ?? null,
      updated_at: detail.updated_at_iso ?? null,
      last_message_text: lastPreview,
    };
  }, [
    detail?.id,
    detail?.status,
    detail?.status_label,
    detail?.queue_line,
    detail?.queue_line_label,
    detail?.action_by,
    detail?.chat_turn,
    detail?.action_since_iso,
    detail?.list_highlight,
    detail?.communication_state,
    detail?.communication_label,
    detail?.updated_at_iso,
    messages,
  ]);

  const clearComposerDrafts = useCallback(() => {
    setReplyTo(null);
    setEditingId(null);
    setEditingAttachments([]);
    setDetachPendingIds(new Set());
    setUploads([]);
    setCommentEditingId(null);
    setCommentDraft("");
  }, []);

  const applyTicketPollSnapshot = useCallback(
    (snap: TicketPollSnapshot) => {
      const prev = detailRef.current;
      if (!prev || !ticketPollSnapshotChanged(prev, snap)) return false;
      if (prev.is_open && !snap.is_open) {
        clearComposerDrafts();
      }
      setDetail(mergeTicketPollSnapshot(prev, snap));
      bumpQueueRefresh();
      return true;
    },
    [clearComposerDrafts, bumpQueueRefresh],
  );

  const applyReadReceiptsUpdate = useCallback((raw: TicketReadReceiptsResult) => {
      const { receipts, readBy } = mergeIncomingReadState(
        readReceiptsRef.current,
        readByReceiptsRef.current,
        raw,
      );
      const receiptsChanged =
        JSON.stringify(receipts) !== JSON.stringify(readReceiptsRef.current);
      const readByChanged =
        JSON.stringify(readBy) !== JSON.stringify(readByReceiptsRef.current);
      if (!receiptsChanged && !readByChanged) return false;
      readReceiptsRef.current = receipts;
      readByReceiptsRef.current = readBy;
      setMessages((prev) => applyReadReceiptsToMessages(prev, receipts, readBy));
      return true;
  }, []);

  const pollReadReceipts = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) return;
    try {
      const res = await fetchTicketReadReceipts(ticketId);
      applyReadReceiptsUpdate(res);
    } catch {
      /* поллинг галочек не мешает чату */
    }
  }, [ticketId, applyReadReceiptsUpdate]);

  const pollMessages = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) return;
    const sinceId = maxLoadedMessageId(messagesRef.current);
    try {
      const res = await fetchTicketMessages(ticketId, { sinceId });
      if (res.ticket) {
        applyTicketPollSnapshot(res.ticket);
      }
      const { receipts, readBy } = mergeIncomingReadState(
        readReceiptsRef.current,
        readByReceiptsRef.current,
        res,
      );
      const hasNew = res.messages.length > 0;
      const receiptsChanged =
        JSON.stringify(receipts) !== JSON.stringify(readReceiptsRef.current);
      const readByChanged =
        JSON.stringify(readBy) !== JSON.stringify(readByReceiptsRef.current);
      if (!hasNew && !receiptsChanged && !readByChanged) return;
      if (hasNew) bumpQueueRefresh();
      readReceiptsRef.current = receipts;
      readByReceiptsRef.current = readBy;
      const inCommentsPanel = chatPanelRef.current === "comments";
      setMessages((prev) => {
        const next = applyReadReceiptsToMessages(
          hasNew ? mergeTicketMessages(prev, res.messages) : prev,
          receipts,
          readBy,
        );
        if (inCommentsPanel) {
          const unread = next.filter((m) => !m.is_initial && m.id > subscriberSeenMaxIdRef.current).length;
          setSubscriberChatUnread(unread);
        }
        return next;
      });
      if (inCommentsPanel) return;
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
  }, [ticketId, applyTicketPollSnapshot, bumpQueueRefresh]);

  const pollComments = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) return;
    const sinceId = maxTicketCommentId(commentsRef.current);
    try {
      const res = await fetchTicketComments(ticketId, { sinceId });
      if (!res.comments.length) return;
      setComments((prev) => mergeTicketComments(prev, res.comments));
      if (atBottomRef.current) {
        requestAnimationFrame(() => {
          const el = scrollRef.current;
          if (el) scrollChatToBottom(el);
        });
      }
    } catch {
      /* поллинг комментариев */
    }
  }, [ticketId]);

  const loadOlderComments = useCallback(async () => {
    if (!commentsHasOlder || commentsLoadingOlderRef.current) return;
    const minId = minTicketCommentId(commentsRef.current);
    if (minId == null) return;
    const el = scrollRef.current;
    if (!el) return;
    commentsLoadingOlderRef.current = true;
    setCommentsLoadingOlder(true);
    const prevHeight = el.scrollHeight;
    const prevTop = el.scrollTop;
    try {
      const res = await fetchTicketComments(ticketId, { beforeId: minId, limit: CHAT_PAGE_SIZE });
      setCommentsHasOlder(Boolean(res.has_older));
      setComments((prev) => mergeTicketComments(prev, res.comments));
      requestAnimationFrame(() => {
        const box = scrollRef.current;
        if (box) preserveScrollOnPrepend(box, prevHeight, prevTop);
      });
    } catch {
      /* тихо */
    } finally {
      commentsLoadingOlderRef.current = false;
      setCommentsLoadingOlder(false);
    }
  }, [ticketId, commentsHasOlder]);

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
      const { receipts, readBy } = mergeIncomingReadState(
        readReceiptsRef.current,
        readByReceiptsRef.current,
        res,
      );
      readReceiptsRef.current = receipts;
      readByReceiptsRef.current = readBy;
      setHasOlder(Boolean(res.has_older));
      setMessages((prev) =>
        applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts, readBy),
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
    if (error || !detail || detail.id !== ticketId) return;
    if (!didInitialAutoscrollRef.current) return;

    const obs = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        if (isLkTicketSource(detail.source) && chatPanel === "comments") void loadOlderComments();
        else void loadOlderMessages();
      },
      {
        root,
        rootMargin: `${CHAT_SCROLL_EDGE_PX}px 0px 0px 0px`,
        threshold: 0,
      },
    );
    obs.observe(target);
    return () => obs.disconnect();
  }, [error, detail, ticketId, chatPanel, loadOlderMessages, loadOlderComments]);

  const loadNewerMessages = useCallback(async () => {
    if (!hasNewer || loadingNewerRef.current) return;
    const maxId = maxLoadedMessageId(messagesRef.current);
    if (maxId <= 0) return;
    loadingNewerRef.current = true;
    setLoadingNewer(true);
    try {
      const res = await fetchTicketMessages(ticketId, { afterId: maxId, limit: CHAT_PAGE_SIZE });
      const { receipts, readBy } = mergeIncomingReadState(
        readReceiptsRef.current,
        readByReceiptsRef.current,
        res,
      );
      readReceiptsRef.current = receipts;
      readByReceiptsRef.current = readBy;
      setHasNewer(Boolean(res.has_newer));
      setMessages((prev) =>
        applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts, readBy),
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
        const { receipts, readBy } = mergeIncomingReadState(
          readReceiptsRef.current,
          readByReceiptsRef.current,
          res,
        );
        readReceiptsRef.current = receipts;
        readByReceiptsRef.current = readBy;
        more = Boolean(res.has_newer);
        setHasNewer(more);
        if (res.messages.length) {
          setMessages((prev) =>
            applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts, readBy),
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

  const jumpToReplyMessage = useCallback(
    async (preview: TicketMessageReplyPreview) => {
      const id = preview.id;
      if (id <= 0 || preview.is_deleted) return;

      if (preview.ticket_id && preview.ticket_id !== ticketId) {
        setCrossTicketMessageId(id);
        return;
      }

      if (!preview.ticket_id) {
        const orphanInView = scrollRef.current?.querySelector(`[data-msg-id="${id}"]`);
        if (orphanInView) {
          orphanInView.scrollIntoView({ behavior: "smooth", block: "center" });
          flashMessage(id);
          return;
        }
        setCrossTicketMessageId(id);
        return;
      }

      const existing = scrollRef.current?.querySelector(`[data-msg-id="${id}"]`);
      if (existing) {
        existing.scrollIntoView({ behavior: "smooth", block: "center" });
        flashMessage(id);
        return;
      }
      try {
        const res = await fetchTicketMessages(ticketId, { aroundId: id, limit: CHAT_PAGE_SIZE });
        const { receipts, readBy } = mergeIncomingReadState(
          readReceiptsRef.current,
          readByReceiptsRef.current,
          res,
        );
        readReceiptsRef.current = receipts;
        readByReceiptsRef.current = readBy;
        setHasOlder(Boolean(res.has_older));
        setHasNewer(Boolean(res.has_newer));
        setMessages((prev) =>
          applyReadReceiptsToMessages(mergeTicketMessages(prev, res.messages), receipts, readBy),
        );
        setPendingNewCount(0);
        atBottomRef.current = false;
        setAtBottom(false);
        requestAnimationFrame(() => {
          const el = scrollRef.current?.querySelector(`[data-msg-id="${id}"]`);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            flashMessage(id);
            return;
          }
          void fetchMessageContext(id)
            .then((ctx) => {
              if (!ctx.ticket_id || ctx.ticket_id !== ticketId) {
                setCrossTicketMessageId(id);
                return;
              }
              window.alert("Не удалось перейти к сообщению");
            })
            .catch((e: unknown) => {
              window.alert(e instanceof Error ? e.message : "Не удалось перейти к сообщению");
            });
        });
      } catch (e: unknown) {
        try {
          const ctx = await fetchMessageContext(id);
          if (!ctx.ticket_id || ctx.ticket_id !== ticketId) {
            setCrossTicketMessageId(id);
            return;
          }
        } catch {
          // fall through
        }
        window.alert(e instanceof Error ? e.message : "Не удалось перейти к сообщению");
      }
    },
    [ticketId, flashMessage],
  );

  useEffect(() => {
    if (error || !detail || detail.id !== ticketId) return;
    const id = window.setInterval(() => void pollMessages(), MSG_POLL_MS);
    return () => window.clearInterval(id);
  }, [error, detail, ticketId, pollMessages]);

  useEffect(() => {
    if (error || !detail || detail.id !== ticketId) return;
    void pollReadReceipts();
    const id = window.setInterval(() => void pollReadReceipts(), READ_RECEIPTS_POLL_MS);
    return () => window.clearInterval(id);
  }, [error, detail, ticketId, pollReadReceipts]);

  useEffect(() => {
    if (
      error ||
      !detail ||
      detail.id !== ticketId ||
      !isLkTicketSource(detail.source) ||
      chatPanel !== "comments"
    ) {
      return;
    }
    const id = window.setInterval(() => void pollComments(), MSG_POLL_MS);
    return () => window.clearInterval(id);
  }, [error, detail, ticketId, chatPanel, pollComments]);

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
  }, [detail?.id, loadOlderMessages, loadNewerMessages, hasNewer]);

  useEffect(() => {
    const id = window.setInterval(() => setNowPulse(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  async function handleTransferToEngineers() {
    if (!detail || transferLoading) return;
    setTransferLoading(true);
    try {
      const next = await transferTicketToEngineers(detail.id);
      setDetail(next);
      bumpQueueRefresh();
      setToast({ message: "Тикет передан инженерам", variant: "success" });
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Не удалось передать тикет",
        variant: "error",
      });
    } finally {
      setTransferLoading(false);
    }
  }

  async function handleReopenTicket() {
    if (!detail || reopenLoading || !detail.can_reopen) return;
    setReopenLoading(true);
    try {
      const next = await reopenTicket(detail.id);
      setDetail(next);
      bumpQueueRefresh();
      setChatPanel("subscriber");
      setCommentEditingId(null);
      setCommentDraft("");
      setReplyTo(null);
      setEditingId(null);
      setToast({ message: "Тикет переоткрыт", variant: "success" });
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Не удалось переоткрыть тикет",
        variant: "error",
      });
    } finally {
      setReopenLoading(false);
    }
  }

  async function handleTakeBackToKs() {
    if (!detail || takeBackLoading) return;
    setTakeBackLoading(true);
    try {
      const next = await takeTicketBackToKs(detail.id);
      setDetail(next);
      bumpQueueRefresh();
      setToast({ message: "Тикет возвращён на линию КС", variant: "success" });
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Не удалось вернуть тикет",
        variant: "error",
      });
    } finally {
      setTakeBackLoading(false);
    }
  }

  async function handleChangePriority(priority: TicketPriority) {
    if (!detail || priorityLoading) return;
    if ((detail.priority || "middle") === priority) return;
    setPriorityLoading(true);
    try {
      const next = await updateTicketPriority(detail.id, priority);
      setDetail(next);
      setToast({ message: "Приоритет обновлён", variant: "success" });
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Не удалось сменить приоритет",
        variant: "error",
      });
    } finally {
      setPriorityLoading(false);
    }
  }

  function setChatPanelMode(mode: TicketChatPanelMode) {
    if (!isLkTicketSource(detail?.source)) return;
    if (mode === chatPanel) return;
    setChatPanel(mode);
    setContextMenu(null);
    setReplyTo(null);
    setEditingId(null);
    setCommentEditingId(null);
    setCommentDraft("");
    if (mode === "comments") {
      subscriberSeenMaxIdRef.current = maxLoadedMessageId(messagesRef.current);
      setSubscriberChatUnread(0);
      if (!comments.length) void loadComments();
      else {
        requestAnimationFrame(() => {
          const el = scrollRef.current;
          if (el) scrollChatToBottom(el);
        });
      }
    } else {
      setSubscriberChatUnread(0);
      subscriberSeenMaxIdRef.current = maxLoadedMessageId(messagesRef.current);
      requestAnimationFrame(() => {
        const el = scrollRef.current;
        if (el) scrollChatToBottom(el);
      });
    }
  }

  function clearComposerMode() {
    setReplyTo(null);
    setEditingId(null);
  }

  function cancelEdit() {
    if (editingId) {
      const orig = messages.find((m) => m.id === editingId);
      editorRef.current?.setContent(orig?.text || "");
      setEditingAttachments(orig?.attachments || []);
    }
    setDetachPendingIds(new Set());
    setEditingId(null);
  }

  function focusComposer() {
    editorRef.current?.focus();
  }

  function applyMacro(macro: HelpdeskMacro) {
    const html = macroTextToEditorHtml(macro.message_text);
    editorRef.current?.setContent(html);
    setEditorEmpty(!html);
    focusComposer();
  }

  function handleEditorEscape() {
    if (editingId) {
      cancelEdit();
    } else if (replyTo) {
      clearComposerMode();
    }
  }

  function handleMessageMenuAction(action: MessageMenuAction, msg: TicketMessage) {
    setContextMenu(null);
    const isCommentsPanel = isLkTicketSource(detail?.source) && chatPanel === "comments";
    if (!detail?.is_open && action !== "copy") return;
    if (action === "copy") {
      const text = msg.text?.trim() || "";
      if (!text) return;
      void navigator.clipboard.writeText(text).catch(() => {
        window.alert("Не удалось скопировать текст");
      });
      return;
    }
    if (action === "reply") {
      if (isCommentsPanel) return;
      setEditingId(null);
      setEditingAttachments([]);
      setReplyTo(msg);
      setUploads([]);
      focusComposer();
      return;
    }
      if (action === "edit") {
      if (isCommentsPanel) {
        const c = comments.find((x) => x.id === msg.id);
        if (!c || !isOwnTicketComment(c)) return;
        setCommentEditingId(c.id);
        setCommentDraft(c.text);
        commentInputRef.current?.focus();
        return;
      }
      setReplyTo(null);
      setEditingId(msg.id);
      setEditingAttachments(msg.attachments || []);
      setDetachPendingIds(new Set());
      setUploads([]);
      requestAnimationFrame(() => {
        editorRef.current?.setContent(msg.text || "");
        editorRef.current?.focus();
      });
      return;
    }
    if (action === "delete") {
      if (isCommentsPanel) {
        const c = comments.find((x) => x.id === msg.id);
        if (c) setCommentDeleteTarget(c);
        return;
      }
      setDeleteTarget(msg);
    }
  }

  async function confirmDeleteComment() {
    if (!commentDeleteTarget) return;
    setDeleting(true);
    try {
      await deleteTicketComment(ticketId, commentDeleteTarget.id);
      setComments((prev) => prev.filter((c) => c.id !== commentDeleteTarget.id));
      if (commentEditingId === commentDeleteTarget.id) {
        setCommentEditingId(null);
        setCommentDraft("");
      }
      setCommentDeleteTarget(null);
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : "Не удалось удалить");
    } finally {
      setDeleting(false);
    }
  }

  async function submitComment() {
    if (!detail?.is_open) return;
    const text = commentDraft.trim();
    if (!text) return;
    setSending(true);
    try {
      if (commentEditingId) {
        const updated = await updateTicketComment(ticketId, commentEditingId, text);
        setComments((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
        setCommentEditingId(null);
      } else {
        const created = await sendTicketComment(ticketId, text);
        setComments((prev) => mergeTicketComments(prev, [created]));
        requestAnimationFrame(() => {
          const el = scrollRef.current;
          if (el) scrollChatToBottom(el);
        });
      }
      setCommentDraft("");
      commentInputRef.current?.focus();
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Не удалось отправить комментарий",
        variant: "error",
      });
    } finally {
      setSending(false);
    }
  }

  function cancelCommentEdit() {
    setCommentEditingId(null);
    setCommentDraft("");
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
        setEditingAttachments([]);
        setDetachPendingIds(new Set());
        editorRef.current?.clear();
      }
      setDeleteTarget(null);
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : "Не удалось удалить");
    } finally {
      setDeleting(false);
    }
  }

  async function submit() {
    if (!detail?.is_open) return;
    if (isLkTicketSource(detail.source) && chatPanel === "comments") {
      await submitComment();
      return;
    }
    const isEmpty = editorRef.current?.isEmpty ?? true;
    const html = isEmpty ? "" : (editorRef.current?.getHTML() ?? "");
    const hasAttachments = editingId ? editingAttachments.length > 0 : uploadSummary.hasReady;
    if (isEmpty && !hasAttachments && !editingId) return;
    if (!detail?.can_reply && detail?.chat_mode === "mail") return;
    if (detail?.subscriber_chat_readonly && !isCommentsPanel) return;
    if (editingId && isEmpty && editingAttachments.length === 0) return;
    if (uploadSummary.pending > 0) {
      autoSendRef.current = true;
      return;
    }

    const skipTextValidation = editingId && isEmpty && editingAttachments.length > 0;
    if (!skipTextValidation) {
      const validation = validateTicketMessage(html, hasAttachments);
      if (!validation.ok) {
        setToast({ message: validation.message, variant: "error" });
        return;
      }
    }

    setSending(true);
    try {
      if (editingId) {
        for (const id of detachPendingIds) {
          if (id > 0) await detachTicketAttachment(ticketId, editingId, id);
        }
        if (isEmpty && editingAttachments.length === 0) {
          await deleteTicketMessage(ticketId, editingId);
          setMessages((prev) => prev.filter((m) => m.id !== editingId));
          setEditingId(null);
          setEditingAttachments([]);
          setDetachPendingIds(new Set());
          editorRef.current?.clear();
          setUploads([]);
          return;
        }
        const updated = await updateTicketMessage(ticketId, editingId, html);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === editingId
              ? { ...m, ...updated, attachments: editingAttachments }
              : m,
          ),
        );
        setEditingId(null);
        setEditingAttachments([]);
        setDetachPendingIds(new Set());
        editorRef.current?.clear();
        setUploads([]);
      } else {
        const created = await sendTicketMessage(ticketId, html, uploadSummary.doneTokens, null, replyTo?.id ?? null);
        if (detail && detail.assigned_to == null && !detail.assignee_is_viewer) {
          setDetail((prev) => (prev ? { ...prev, assignee_is_viewer: true } : prev));
        }
        void fetchTicketDetail(ticketId)
          .then((next) => {
            setDetail(next);
            bumpQueueRefresh();
          })
          .catch(() => {});
        flushSync(() => {
          if (created.length) {
            setMessages((prev) =>
              applyReadReceiptsToMessages(
                mergeTicketMessages(prev, created),
                readReceiptsRef.current,
                readByReceiptsRef.current,
              ),
            );
          }
          setAtBottom(true);
          setPendingNewCount(0);
          setHasNewer(false);
        });
        atBottomRef.current = true;
        editorRef.current?.clear();
        setUploads([]);
        setReplyTo(null);
        const el = scrollRef.current;
        if (el) scrollChatToBottom(el);
        void pollReadReceipts();
      }
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : editingId ? "Не удалось сохранить" : "Не удалось отправить");
    } finally {
      setSending(false);
    }
  }

  useEffect(() => {
    if (!autoSendRef.current) return;
    if (uploadSummary.pending > 0) return;
    autoSendRef.current = false;
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    submit();
  }, [uploadSummary.pending]); // submit зависит от большого набора state; триггерим только по смене pending

  async function enqueueFiles(list: FileList | File[]) {
    const arr = Array.from(list || []);
    if (!arr.length) return;
    try {
      // Снимок байтов до сброса input — иначе File может стать пустым в части браузеров
      const snapshots = await Promise.all(
        arr.map(async (f) => {
          try {
            const buf = await f.arrayBuffer();
            return new File([buf], f.name || "file", {
              type: f.type || "application/octet-stream",
              lastModified: f.lastModified || Date.now(),
            });
          } catch {
            return f;
          }
        }),
      );
      const normalized: File[] = [];
      for (const f of snapshots) {
        if (f.type.startsWith("image/")) {
          normalized.push(await compressImageToWebp(f));
        } else {
          normalized.push(f);
        }
      }
      const items = normalized.map((file) => {
        let previewUrl: string | undefined;
        if (file.type.startsWith("image/")) {
          try {
            previewUrl = URL.createObjectURL(file);
          } catch {
            previewUrl = undefined;
          }
        }
        return {
          id: newUploadId(),
          file,
          previewUrl,
          status: "pending" as const,
          uploaded: 0,
          total: file.size || 0,
          isImage: file.type.startsWith("image/"),
        };
      });
      setUploads((prev) => [...prev, ...items]);
    } catch (e) {
      console.error("enqueueFiles failed", e);
      window.alert(e instanceof Error ? e.message : "Не удалось добавить файлы");
    }
  }

  useEffect(() => {
    return () => {
      for (const u of uploads) {
        if (u.previewUrl) URL.revokeObjectURL(u.previewUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // один активный XHR, не abort на каждом ре-рендере
    if (uploadingIdRef.current) return;
    const next = uploads.find((u) => u.status === "pending");
    if (!next) return;

    setUploads((prev) => prev.map((u) => (u.id === next.id ? { ...u, status: "uploading" } : u)));
    const xhr = new XMLHttpRequest();
    uploadingXhrRef.current = xhr;
    uploadingIdRef.current = next.id;
    xhr.open("POST", `/api/v1/helpdesk/tracker/${ticketId}/attachments/upload`);
    xhr.withCredentials = true;
    xhr.upload.onprogress = (e) => {
      if (!e.lengthComputable) return;
      setUploads((prev) =>
        prev.map((u) => (u.id === next.id ? { ...u, uploaded: e.loaded, total: e.total } : u)),
      );
    };
    xhr.onerror = () => {
      setUploads((prev) =>
        prev.map((u) => (u.id === next.id ? { ...u, status: "error", err: "Ошибка загрузки" } : u)),
      );
      if (uploadingXhrRef.current === xhr) uploadingXhrRef.current = null;
      if (uploadingIdRef.current === next.id) uploadingIdRef.current = null;
    };
    xhr.onload = () => {
      if (xhr.status < 200 || xhr.status >= 300) {
        setUploads((prev) =>
          prev.map((u) =>
            u.id === next.id ? { ...u, status: "error", err: `HTTP ${xhr.status}` } : u,
          ),
        );
      } else {
        try {
          const data = JSON.parse(xhr.responseText) as { token: string; is_image: boolean };
          if (!data?.token) throw new Error("no token");
          setUploads((prev) =>
            prev.map((u) =>
              u.id === next.id
                ? {
                    ...u,
                    status: "done",
                    token: data.token,
                    isImage: Boolean(data.is_image),
                    uploaded: u.total,
                    total: u.total,
                  }
                : u,
            ),
          );
        } catch {
          setUploads((prev) =>
            prev.map((u) => (u.id === next.id ? { ...u, status: "error", err: "Некорректный ответ" } : u)),
          );
        }
      }
      if (uploadingXhrRef.current === xhr) uploadingXhrRef.current = null;
      if (uploadingIdRef.current === next.id) uploadingIdRef.current = null;
    };
    const fd = new FormData();
    fd.set("file", next.file);
    try {
      xhr.send(fd);
    } catch {
      setUploads((prev) =>
        prev.map((u) => (u.id === next.id ? { ...u, status: "error", err: "Не удалось начать загрузку" } : u)),
      );
      if (uploadingXhrRef.current === xhr) uploadingXhrRef.current = null;
      if (uploadingIdRef.current === next.id) uploadingIdRef.current = null;
    }
  }, [uploads, ticketId]);

  useEffect(() => {
    // abort только при смене тикета/размонтаже
    return () => {
      try {
        uploadingXhrRef.current?.abort();
      } catch {
        /* ignore */
      }
      uploadingXhrRef.current = null;
      uploadingIdRef.current = null;
    };
  }, [ticketId]);

  const isSwitchingTicket = detail != null && detail.id !== ticketId;

  const closeMobilePanel = useCallback(() => setMobilePanel(null), []);

  const openKbArticle = useCallback((slug: string) => {
    setHelperCollapsed(false);
    setKbArticleSlug(slug);
  }, []);

  const closeKbArticle = useCallback(() => setKbArticleSlug(null), []);

  const toggleMobilePanel = useCallback((panel: "queue" | "info") => {
    setMobilePanel((current) => (current === panel ? null : panel));
  }, []);

  useEffect(() => {
    if (!isMobileLayout) setMobilePanel(null);
  }, [isMobileLayout]);

  useEffect(() => {
    setMobilePanel(null);
  }, [ticketId]);

  useEffect(() => {
    if (!mobilePanel) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMobilePanel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobilePanel, closeMobilePanel]);

  const viewportPanelClass =
    isMobileLayout && mobilePanel === "queue"
      ? " tk-cc-viewport--panel-queue"
      : isMobileLayout && mobilePanel === "info"
        ? " tk-cc-viewport--panel-info"
        : "";

  function renderMobileQueueButton() {
    if (!isMobileLayout) return null;
    return (
      <button
        type="button"
        className={`tk-cc-mobile-btn${mobilePanel === "queue" ? " tk-cc-mobile-btn--on" : ""}`}
        aria-label="Очередь тикетов"
        title="Очередь тикетов"
        onClick={() => toggleMobilePanel("queue")}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path d="M4 6h16M4 12h16M4 18h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>
    );
  }

  function renderMobileInfoButton() {
    if (!isMobileLayout) return null;
    return (
      <button
        type="button"
        className={`tk-cc-mobile-btn${mobilePanel === "info" ? " tk-cc-mobile-btn--on" : ""}`}
        aria-label="Данные абонента и тикета"
        title="Данные абонента"
        onClick={() => toggleMobilePanel("info")}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="2" />
          <path d="M5 20c0-3.3 3.1-5 7-5s7 1.7 7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>
    );
  }

  if (!detail) {
    return (
      <div className="tp on" id="tp-ticket">
        <div className={`tk-cc-viewport${viewportPanelClass}`}>
          {isMobileLayout && mobilePanel ? (
            <button
              type="button"
              className="tk-cc-mobile-backdrop"
              aria-label="Закрыть панель"
              onClick={closeMobilePanel}
            />
          ) : null}
          <TicketQueueSidebar
            activeTicketId={ticketId}
            activeTicketSync={activeTicketQueueSync}
            refreshNonce={queueRefreshNonce}
            onTicketSelect={closeMobilePanel}
            onClose={isMobileLayout ? closeMobilePanel : undefined}
          />
          <div className="tk-cc-helper-wrap" aria-hidden>
            <section className="tk-cc-helper tk-cc-helper--placeholder" />
          </div>
          <div className="tk-cc-chat">
            <header className="tk-cc-chat__head">
              <div className="tk-cc-chat__head-main">
                {renderMobileQueueButton()}
                <div className="tk-cc-chat__head-left">
                  <span className="tk-cc-chat__title">Тикет #{ticketId}</span>
                </div>
                {renderMobileInfoButton()}
              </div>
            </header>
            <div className="tk-chat-main tk-cc-chat__body">
              <div className="tk-chat-viewport">
                <div className="cscrl tk-chat-scroll">
                  {error ? (
                    <div className="tk-chat-empty">
                      <div className="ch-list-err">{error}</div>
                      <Link to="/tickets" className="tk-back-link">
                        ← К тикетам
                      </Link>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        </div>
        {toast ? (
          <ToastNotice
            message={toast.message}
            variant={toast.variant}
            durationMs={3000}
            onClose={() => setToast(null)}
          />
        ) : null}
      </div>
    );
  }

  const subscriberSidebarName =
    detail.subscriber_name?.trim() || detail.caller_name?.trim() || "Абонент";
  const subscriberChatName = (() => {
    const short = detail.subscriber_display_name?.trim();
    if (short && short !== "Абонент") return short;
    if (detail.subscriber_is_juridical === 2) return subscriberSidebarName;
    const parts = subscriberSidebarName.split(/\s+/);
    return parts.length >= 2 ? parts[1] : subscriberSidebarName;
  })();
  const introBody = detail.body?.trim() || "";
  const introPlain = introBody
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  const chatMessages = messages.filter((m) => !m.is_initial);
  const isLkTicket = isLkTicketSource(detail.source);
  const isCommentsPanel = isLkTicket && chatPanel === "comments";
  const subscriberChatReadonly = Boolean(detail.subscriber_chat_readonly) && !isCommentsPanel;
  const hideQuickReplies = !isLkTicket;
  const feedMessages = isCommentsPanel ? comments.map(commentToMessage) : chatMessages;
  const hasIntro = !isCommentsPanel && introPlain.length > 0;
  const feedLoadingOlder = isCommentsPanel ? commentsLoadingOlder : loadingOlder;
  const online = Boolean(detail.user_id) ? Boolean(detail.subscriber_online) : false;
  const offlineAuthLabel = subscriberProfile?.online.last_session_end_label?.trim() || null;
  const onlineStatusLabel = online
    ? "Абонент онлайн"
    : offlineAuthLabel
      ? `Офлайн · последняя авторизация ${offlineAuthLabel}`
      : "Абонент офлайн";

  function handleFeedContextMenu(e: React.MouseEvent, m: TicketMessage) {
    if (!detail.is_open) {
      if (isCommentsPanel) return;
      if (!m.text?.trim()) return;
      e.preventDefault();
      e.stopPropagation();
      setContextMenu({ x: e.clientX, y: e.clientY, msg: m });
      return;
    }
    if (isCommentsPanel) {
      e.preventDefault();
      e.stopPropagation();
      const c = commentsRef.current.find((x) => x.id === m.id);
      if (!c || !isOwnTicketComment(c)) return;
      setContextMenu({ x: e.clientX, y: e.clientY, msg: m });
      return;
    }
    if (!canMessageContextMenu(m.side, m.id)) return;
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, msg: m });
  }

  function renderFeedMessage(m: TicketMessage) {
    const authorLabel = isCommentsPanel
      ? m.author_name || ticketAuthorLabel(m, subscriberChatName)
      : ticketAuthorLabel(m, subscriberChatName);
    const displayTimeIso =
      m.is_edited && m.updated_at_iso ? m.updated_at_iso : m.created_at_iso;
    const timeLabel = formatMsgTime(displayTimeIso) || "—";
    const editedSuffix =
      m.is_edited ? (
        <span
          className="tk-msg-edited"
          title={
            m.created_at_iso && m.updated_at_iso
              ? `Создано: ${formatMsgTime(m.created_at_iso)}`
              : m.updated_at_iso || undefined
          }
        >
          {" "}
          · изм.
        </span>
      ) : null;

    if (m.side === "bot") {
      return (
        <div key={m.id} className="tk-tg-bubble tk-tg-bubble--bot" data-msg-id={m.id}>
          <div className="tk-tg-bubble__info">{authorLabel} · {timeLabel}</div>
          <div className="tk-tg-bubble__body tk-tg-bubble__body--bot">
            <MessageBody text={m.text} />
            <TicketMessageAttachments msg={m} onOpenImage={openImageViewer} />
          </div>
        </div>
      );
    }

    const outgoing = m.side === "me";
    const engineer = isEngineerTicketMessage(m);
    return (
      <div
        key={m.id}
        data-msg-id={m.id}
        className={`tk-tg-bubble${outgoing ? " tk-tg-bubble--out" : " tk-tg-bubble--in"}${engineer ? " tk-tg-bubble--engineer" : ""}${highlightId === m.id ? " tk-tg-bubble--highlight" : ""}`}
        onContextMenu={(e) => handleFeedContextMenu(e, m)}
      >
        <div className="tk-tg-bubble__info">
          {outgoing ? "Вы" : authorLabel} · {timeLabel}
          {editedSuffix}
        </div>
        <div
          className={`tk-tg-bubble__body${outgoing ? " tk-tg-bubble__body--out" : ""}${engineer ? " tk-tg-bubble__body--engineer" : ""}`}
        >
          {!isCommentsPanel && m.reply_preview ? (
            <TicketMessageReplyQuote preview={m.reply_preview} onJump={jumpToReplyMessage} />
          ) : null}
          <MessageBody text={m.text} />
          {!isCommentsPanel ? <TicketMessageAttachments msg={m} onOpenImage={openImageViewer} /> : null}
          {!isCommentsPanel && outgoing ? (
            <div className="tk-tg-bubble__ticks">
              <TicketDeliveryTicks
                side={m.side}
                recipientReadAtIso={m.recipient_read_at_iso}
                readBy={m.read_by}
              />
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="tp on" id="tp-ticket">
      <div className={`tk-cc-viewport${isSwitchingTicket ? " tk-cc-viewport--switching" : ""}${viewportPanelClass}`}>
        {isMobileLayout && mobilePanel ? (
          <button
            type="button"
            className="tk-cc-mobile-backdrop"
            aria-label="Закрыть панель"
            onClick={closeMobilePanel}
          />
        ) : null}
        <div className="tk-cc-left-rail">
          <TicketQueueSidebar
            activeTicketId={ticketId}
            activeTicketSync={activeTicketQueueSync}
            refreshNonce={queueRefreshNonce}
            onTicketSelect={closeMobilePanel}
            onClose={isMobileLayout ? closeMobilePanel : undefined}
          />

          <TicketHelperPanel
            detail={detail}
            profile={subscriberProfile}
            collapsed={isMobileLayout ? false : kbArticleSlug ? false : helperCollapsed}
            onToggle={() => setHelperCollapsed((v) => !v)}
            nowPulse={nowPulse}
            checkCache={checkCache}
            onCheckCache={setCheckCache}
            onDisconnect={() =>
              postDisconnect(detail.user_id!).then(() => {
                void load();
              })
            }
            transferLoading={transferLoading}
            takeBackLoading={takeBackLoading}
            reopenLoading={reopenLoading}
            priorityLoading={priorityLoading}
            onTransfer={() => void handleTransferToEngineers()}
            onTakeBack={() => void handleTakeBackToKs()}
            onReopen={() => void handleReopenTicket()}
            onChangePriority={(p) => void handleChangePriority(p)}
            onLinkSubscriber={() => setLinkSubscriberOpen(true)}
            onOpenKbArticle={openKbArticle}
            kbArticleOpen={Boolean(kbArticleSlug)}
            onMobileClose={isMobileLayout ? closeMobilePanel : undefined}
          />

          {kbArticleSlug ? (
            <TicketKbArticleOverlay slug={kbArticleSlug} onClose={closeKbArticle} />
          ) : null}
        </div>

        <div className={`tk-cc-chat${isCommentsPanel ? " tk-cc-chat--comments" : ""}`}>
          <header className="tk-cc-chat__head">
            <div className="tk-cc-chat__head-main">
              {renderMobileQueueButton()}
              <div className="tk-cc-chat__head-left">
                <div className="tk-cc-chat__identity">
                  <div className="tk-cc-chat__identity-row">
                    {detail.subscriber_profile_user_id != null ? (
                      <Link to={`/users/${detail.subscriber_profile_user_id}`} className="tk-cc-chat__title">
                        {subscriberSidebarName}
                      </Link>
                    ) : (
                      <span className="tk-cc-chat__title">{subscriberSidebarName}</span>
                    )}
                    <span className={`tk-cc-online${online ? " tk-cc-online--on" : " tk-cc-online--off"}`}>
                      {onlineStatusLabel}
                    </span>
                  </div>
                  <span className="tk-cc-chat__ticket-meta" title={detail.title}>
                    #{detail.id} · {detail.title}
                  </span>
                </div>
              </div>
              {renderMobileInfoButton()}
            </div>
          </header>

          <div className={`tk-chat-main tk-cc-chat__body${isCommentsPanel ? " tk-chat-main--comments" : ""}`}>
            <div className="tk-chat-viewport">
              <div
                className="cscrl tk-chat-scroll"
                ref={scrollRef}
                onContextMenu={
                  isCommentsPanel
                    ? (e) => {
                        e.preventDefault();
                      }
                    : undefined
                }
              >
                <div className="tk-chat-feed">
                <div ref={topSentinelRef} style={{ height: 1 }} aria-hidden />
                {feedLoadingOlder ? (
                  <div className="tk-chat-load-hint" aria-live="polite">
                    Загрузка предыдущих сообщений…
                  </div>
                ) : null}
                {isCommentsPanel ? (
                  <div className="tk-chat-comments-banner" role="note">
                    Служебные комментарии — абонент их не видит
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

                {feedMessages.length > 0 && hasIntro ? (
                  <div className="tk-chat-divider" aria-hidden>
                    <span>Переписка</span>
                  </div>
                ) : null}

                {feedMessages.length === 0 && !hasIntro ? (
                  <div className="tk-chat-empty">
                    {isCommentsPanel ? "Комментариев пока нет" : "Сообщений пока нет"}
                  </div>
                ) : (
                  feedMessages.map((m) => renderFeedMessage(m))
                )}
                {loadingNewer ? (
                  <div className="tk-chat-load-hint tk-chat-load-hint--bottom" aria-live="polite">
                    Загрузка…
                  </div>
                ) : null}
              </div>
            </div>
              {!isCommentsPanel ? (
                <TicketChatScrollDown
                  visible={!atBottom}
                  pendingCount={pendingNewCount}
                  onClick={() => void goToChatBottom()}
                />
              ) : null}
            </div>

            <div className={`tk-composer${isCommentsPanel ? " tk-composer--comments" : ""}`}>
              {!detail.is_open ? (
                <>
                  {isLkTicket ? (
                    <TicketMacroBar
                      hideMacros
                      onPick={applyMacro}
                      chatPanel={chatPanel}
                      onChatPanelChange={setChatPanelMode}
                      subscriberUnreadCount={subscriberChatUnread}
                    />
                  ) : null}
                  <div className="tk-closed-bar">
                    <div className="tk-no-reply">
                      {isCommentsPanel
                        ? "Тикет закрыт — служебные комментарии доступны только для просмотра"
                        : "Тикет закрыт — переписка доступна только для просмотра"}
                    </div>
                    {detail.can_reopen ? (
                      <button
                        type="button"
                        className="tb3 tk-reopen-btn"
                        disabled={reopenLoading}
                        onClick={() => void handleReopenTicket()}
                      >
                        {reopenLoading ? "Открываю…" : "Переоткрыть"}
                      </button>
                    ) : null}
                  </div>
                </>
              ) : isCommentsPanel ? (
                <>
                  <TicketMacroBar
                    hideMacros={hideQuickReplies}
                    disabled={sending}
                    onPick={applyMacro}
                    chatPanel={chatPanel}
                    onChatPanelChange={setChatPanelMode}
                    subscriberUnreadCount={subscriberChatUnread}
                  />
                  {commentEditingId ? (
                    <div className="tk-composer-mode tk-composer-mode--edit">
                      <div className="tk-composer-mode__label">Редактирование комментария</div>
                      <button
                        type="button"
                        className="tk-composer-mode__close"
                        onClick={cancelCommentEdit}
                        aria-label="Отменить редактирование"
                      >
                        ×
                      </button>
                    </div>
                  ) : null}
                  <div className="tk-composer__box tk-composer__box--plain">
                    <textarea
                      ref={commentInputRef}
                      className="tk-comment-input"
                      value={commentDraft}
                      placeholder="Комментарий для коллег… Ctrl + Enter — отправить"
                      disabled={sending}
                      rows={2}
                      onChange={(e) => setCommentDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          e.preventDefault();
                          cancelCommentEdit();
                          return;
                        }
                        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                          e.preventDefault();
                          void submitComment();
                        }
                      }}
                    />
                    <button
                      type="button"
                      className="tk-composer__send"
                      disabled={sending || !commentDraft.trim()}
                      onClick={() => void submitComment()}
                      title={commentEditingId ? "Сохранить" : "Отправить"}
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
                </>
              ) : subscriberChatReadonly ? (
                <div className="tk-no-reply" role="note">
                  Режим просмотра — отправка сообщений абоненту недоступна
                </div>
              ) : !detail.can_reply && detail.chat_mode === "mail" ? (
                <div className="tk-no-reply">
                  Абонент не определён — ответ в личном кабинете недоступен. Привяжите абонента в карточке
                  тикета.
                </div>
              ) : (
                <>
                  {!editingId && isLkTicket ? (
                    <TicketMacroBar
                      hideMacros={hideQuickReplies}
                      disabled={sending}
                      onPick={applyMacro}
                      chatPanel={chatPanel}
                      onChatPanelChange={setChatPanelMode}
                      subscriberUnreadCount={subscriberChatUnread}
                    />
                  ) : null}
                  {replyTo ? (
                    <div className="tk-composer-mode">
                      <div className="tk-composer-mode__label">Ответ на сообщение</div>
                      <TicketMessageReplyQuote
                        preview={
                          replyTo.reply_preview ?? {
                            id: replyTo.id,
                            author_name: ticketAuthorLabel(replyTo, subscriberChatName),
                            text: replyTo.text,
                          }
                        }
                        onJump={jumpToReplyMessage}
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
                  <div className="tk-composer__box">
                    <RichEditor
                      ref={editorRef}
                      placeholder={
                        editingId
                          ? "Измените текст сообщения… Ctrl + Enter — сохранить"
                          : replyTo
                            ? "Ваш ответ… Ctrl + Enter — отправить"
                            : "Ответ клиенту… Ctrl + Enter — отправить"
                      }
                      disabled={sending}
                      onSubmit={submit}
                      onEscape={handleEditorEscape}
                      onChange={setEditorEmpty}
                      onPasteFiles={editingId ? undefined : enqueueFiles}
                      rightActions={
                        <>
                          {editingId ? (
                            <button
                              type="button"
                              className="tk-composer__cancel-edit"
                              disabled={sending}
                              onClick={cancelEdit}
                            >
                              Отмена
                            </button>
                          ) : (
                            <label className="tk-composer__attach" title="Прикрепить файл">
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
                                multiple
                                accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
                                onChange={(e) => {
                                  const input = e.currentTarget;
                                  const files = Array.from(input.files || []);
                                  input.value = "";
                                  if (files.length) void enqueueFiles(files);
                                }}
                              />
                            </label>
                          )}
                          <button
                            type="button"
                            className="tk-composer__send"
                            disabled={sending || (editingId ? (editorEmpty && editingAttachments.length === 0) : (editorEmpty && !uploadSummary.hasReady))}
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
                        </>
                      }
                    />
                  </div>
                  {uploads.length ? (
                    <div className="tk-upq" onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
                      e.preventDefault();
                      if (editingId) return;
                      void enqueueFiles(e.dataTransfer.files);
                    }}>
                      <div className="tk-upq__top">
                        <span>
                          Загружено: {formatBytes(uploadSummary.uploaded)} / {formatBytes(uploadSummary.total)}
                        </span>
                        <button
                          type="button"
                          className="tk-upq__clear"
                          disabled={sending}
                          onClick={() => {
                            setUploads((prev) => {
                              for (const u of prev) if (u.previewUrl) URL.revokeObjectURL(u.previewUrl);
                              return [];
                            });
                          }}
                        >
                          Очистить
                        </button>
                      </div>
                      <div className="tk-upq__items">
                        {uploads.map((u) => (
                          <div key={u.id} className={`tk-upq__item tk-upq__item--${u.status}`}>
                            {u.previewUrl ? (
                              <button
                                type="button"
                                className="tk-upq__thumb"
                                onClick={() => {
                                  setPreviewUrl(u.previewUrl || null);
                                  setPreviewOpen(Boolean(u.previewUrl));
                                }}
                                aria-label="Открыть изображение"
                                title="Открыть изображение"
                              >
                                <img src={u.previewUrl} alt={u.file.name} />
                              </button>
                            ) : (
                              <div className="tk-upq__thumb tk-upq__thumb--file" aria-hidden>
                                <FileBadge filename={u.file.name} />
                              </div>
                            )}
                            <span className="tk-upq__name" title={u.file.name}>{truncateFilename(u.file.name)}</span>
                            <span className="tk-upq__meta">
                              {formatBytes(u.total)}{u.status === "uploading" ? ` · ${Math.round((u.uploaded / Math.max(1, u.total)) * 100)}%` : ""}
                              {u.status === "error" && u.err ? ` · ${u.err}` : ""}
                            </span>
                            <button
                              type="button"
                              className="tk-upq__rm"
                              disabled={sending}
                              onClick={() =>
                                setUploads((prev) => {
                                  const cur = prev.find((x) => x.id === u.id);
                                  if (cur?.status === "uploading" && uploadingIdRef.current === u.id) {
                                    try {
                                      uploadingXhrRef.current?.abort();
                                    } catch {
                                      /* ignore */
                                    }
                                  }
                                  if (cur?.previewUrl) URL.revokeObjectURL(cur.previewUrl);
                                  return prev.filter((x) => x.id !== u.id);
                                })
                              }
                              aria-label="Убрать файл"
                              title="Убрать файл"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {editingId && editingAttachments.length ? (
                    <div className="tk-edatt">
                      <div className="tk-edatt__head">Вложения сообщения</div>
                      <div className="tk-edatt__items">
                        {editingAttachments.map((a) => (
                          <div key={a.id} className="tk-edatt__item">
                            {a.is_image ? (
                              <button
                                type="button"
                                className="tk-edatt__thumb"
                                onClick={() => openImageViewer(a.file_path)}
                                title={a.original_filename || "Открыть"}
                              >
                                <AttachmentImage src={a.file_path} alt={a.original_filename || "Вложение"} />
                              </button>
                            ) : (
                              <a
                                className="tk-edatt__thumb tk-edatt__thumb--file"
                                href={a.file_path}
                                target="_blank"
                                rel="noreferrer"
                                title={a.original_filename || "Открыть файл"}
                                aria-label={a.original_filename || "Открыть файл"}
                              >
                                <FileBadge filename={a.original_filename} />
                              </a>
                            )}
                            <span className="tk-edatt__name" title={a.original_filename || undefined}>
                              {truncateFilename(a.original_filename || "Файл")}
                            </span>
                            <span className="tk-edatt__meta">
                              {a.file_size_bytes ? formatBytes(a.file_size_bytes) : ""}
                            </span>
                            <button
                              type="button"
                              className="tk-edatt__rm"
                              disabled={sending}
                              onClick={() => {
                                if (a.id > 0) {
                                  setDetachPendingIds((prev) => {
                                    const next = new Set(prev);
                                    next.add(a.id);
                                    return next;
                                  });
                                }
                                setEditingAttachments((prev) => prev.filter((x) => x.id !== a.id));
                              }}
                              aria-label="Удалить вложение"
                              title="Удалить вложение"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </>
              )}
            </div>
          </div>

          {contextMenu ? (
            <TicketMessageContextMenu
              x={contextMenu.x}
              y={contextMenu.y}
              message={contextMenu.msg}
              allowReply={!isCommentsPanel && detail.is_open && !subscriberChatReadonly}
              commentMode={isCommentsPanel && detail.is_open}
              readOnly={!detail.is_open || subscriberChatReadonly}
              onAction={handleMessageMenuAction}
              onClose={() => setContextMenu(null)}
            />
          ) : null}

          <TicketDeleteMessageModal
            open={Boolean(deleteTarget || commentDeleteTarget)}
            busy={deleting}
            onClose={() => {
              if (!deleting) {
                setDeleteTarget(null);
                setCommentDeleteTarget(null);
              }
            }}
            onConfirm={() => void (commentDeleteTarget ? confirmDeleteComment() : confirmDelete())}
          />

        </div>
      </div>

      {previewOpen && previewUrl ? (
        <div
          className="tk-imgv"
          role="dialog"
          aria-modal="true"
          onClick={() => {
            setPreviewOpen(false);
            setPreviewUrl(null);
          }}
        >
          <div
            className="tk-imgv__box"
            onClick={(e) => {
              e.stopPropagation();
            }}
          >
            <button
              type="button"
              className="tk-imgv__close"
              aria-label="Закрыть"
              onClick={() => {
                setPreviewOpen(false);
                setPreviewUrl(null);
              }}
            >
              ×
            </button>
            <img className="tk-imgv__img" src={previewUrl} alt="Просмотр" />
          </div>
        </div>
      ) : null}

      {imgViewerOpen && allImageUrls.length ? (
        <div
          className="tk-imgv"
          role="dialog"
          aria-modal="true"
          onClick={() => setImgViewerOpen(false)}
        >
          <button type="button" className="tk-imgv__close" aria-label="Закрыть" onClick={() => setImgViewerOpen(false)}>
            ×
          </button>
          <button
            type="button"
            className="tk-imgv__nav tk-imgv__nav--prev"
            aria-label="Предыдущее"
            onClick={(e) => {
              e.stopPropagation();
              setImgViewerIndex((i) => {
                const newIdx = allImageUrls.length ? (i - 1 + allImageUrls.length) % allImageUrls.length : 0;
                imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                return newIdx;
              });
            }}
          >
            ‹
          </button>
          <div className="tk-imgv__box" onClick={(e) => e.stopPropagation()}>
            <img className="tk-imgv__img" src={allImageUrls[Math.min(imgViewerIndex, allImageUrls.length - 1)]} alt="Просмотр" />
            <div className="tk-imgv__counter" aria-live="polite">
              {imgViewerIndex + 1} / {allImageUrls.length}
            </div>
          </div>
          <button
            type="button"
            className="tk-imgv__nav tk-imgv__nav--next"
            aria-label="Следующее"
            onClick={(e) => {
              e.stopPropagation();
              setImgViewerIndex((i) => {
                const newIdx = allImageUrls.length ? (i + 1) % allImageUrls.length : 0;
                imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                return newIdx;
              });
            }}
          >
            ›
          </button>
        </div>
      ) : null}

      <TicketLinkSubscriberModal
        open={linkSubscriberOpen}
        ticketId={detail.id}
        onClose={() => setLinkSubscriberOpen(false)}
        onLinked={(next) => {
          setDetail(next);
          setToast({ message: "Абонент привязан к тикету", variant: "success" });
        }}
      />

      <TicketCrossTicketMessageModal
        open={crossTicketMessageId != null}
        messageId={crossTicketMessageId ?? 0}
        currentTicketId={ticketId}
        subscriberName={subscriberChatName}
        onClose={() => setCrossTicketMessageId(null)}
      />

      {toast ? (
        <ToastNotice
          message={toast.message}
          variant={toast.variant}
          durationMs={3000}
          onClose={() => setToast(null)}
        />
      ) : null}
    </div>
  );
}
