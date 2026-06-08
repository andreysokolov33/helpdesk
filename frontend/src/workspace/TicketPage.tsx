import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import RichEditor, { type RichEditorHandle } from "@/components/RichEditor";
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
  isLkTicketSource,
  priorityBadgeClass,
  sourceBadgeClass,
  queueLineBadgeClass,
  queueLineShortLabel,
} from "@/utils/ticketLabels";
import {
  fetchTicketDetail,
  fetchTicketMessages,
  fetchTicketReadReceipts,
  formatMsgTime,
  formatTicketCreated,
  closeTicket,
  reopenTicket,
  deleteTicketMessage,
  sendTicketMessage,
  takeTicketBackToKs,
  transferTicketToEngineers,
  updateTicketMessage,
  uploadTicketAttachment,
  detachTicketAttachment,
  type TicketDetail,
  type TicketMessage,
  type TicketMessageReadBy,
  type TicketReadReceiptsResult,
} from "@/api/ticket";
import type { TicketCategoryLeaf } from "@/api/ticketCategories";
import {
  applyReadReceiptsToMessages,
  canMessageContextMenu,
  mergeIncomingReadState,
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
  watchChatScrollToBottom,
} from "@/utils/ticketChatScroll";
import { compressImageToWebp } from "@/utils/imageCompress";
import { formatBytes } from "@/utils/formatBytes";
import FileBadge, { resolveFileExt, truncateFilename } from "@/components/FileBadge";
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
import TicketSubscriberAccountSidebar from "@/components/TicketSubscriberAccountSidebar";
import TicketLinkSubscriberModal from "@/workspace/TicketLinkSubscriberModal";
import { macroTextToEditorHtml, type HelpdeskMacro } from "@/api/macros";
import { validateTicketMessage } from "@/utils/ticketMessageValidation";

const MSG_POLL_MS = 5000;
const READ_RECEIPTS_POLL_MS = 3000;

function AttachmentImage({ src, alt }: { src: string; alt: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <span className="tk-att-img__nophoto">
        <span className="tk-att-img__nophoto-icon">🖼</span>
        Нет фото
      </span>
    );
  }
  return <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />;
}

type AttachBlockProps = { msg: TicketMessage };

function AttachmentsBlock({
  msg,
  onOpenImage,
}: AttachBlockProps & {
  onOpenImage: (url: string) => void;
}) {
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
  const images = items.filter((a) => Boolean(a.is_image));
  const files = items.filter((a) => !a.is_image);
  const n = images.length;
  return (
    <div className="tk-att">
      {images.length ? (
        <div className={`tk-att-grid tk-att-grid--n${Math.min(5, n)}`}>
          {images.map((a) => (
            <button
              key={a.id}
              type="button"
              className="tk-att-img"
              onClick={() => onOpenImage(a.file_path)}
              title={a.original_filename || "Открыть изображение"}
            >
              <AttachmentImage src={a.file_path} alt={a.original_filename || "Вложение"} />
            </button>
          ))}
        </div>
      ) : null}
      {files.length ? (
        <div className="tk-att-files">
          {files.map((a) => (
            <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-file">
              <FileBadge filename={a.original_filename} ext={resolveFileExt(a.original_filename)} />
              <span className="tk-att-file__name" title={a.original_filename || undefined}>
                {truncateFilename(a.original_filename || "Файл")}
              </span>
            </a>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function TicketPage() {
  const { ticketId: ticketIdParam } = useParams();
  const ticketId = Number(ticketIdParam);
  const navigate = useNavigate();
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
  const [editorEmpty, setEditorEmpty] = useState(true);
  const [sending, setSending] = useState(false);
  const [sideOpen, setSideOpen] = useState(true);
  const [classifyOpen, setClassifyOpen] = useState(false);
  const [classifyAction, setClassifyAction] = useState<ClassifyAction>("close");
  const [classifyConfirming, setClassifyConfirming] = useState(false);
  const [takeBackLoading, setTakeBackLoading] = useState(false);
  const [reopenLoading, setReopenLoading] = useState(false);
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
  const [checkOpen, setCheckOpen] = useState(false);
  const [checkCache, setCheckCache] = useState<FastCheckResponse | null>(null);
  const [checkLoading, setCheckLoading] = useState(false);
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
  }, [ticketId]);

  useEffect(() => {
    chatPanelRef.current = chatPanel;
  }, [chatPanel]);

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
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
      setDetail(null);
      setMessages([]);
      setHasOlder(false);
      setHasNewer(false);
      readReceiptsRef.current = {};
      readByReceiptsRef.current = {};
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

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
    if (loading || error || !detail) return;
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
  }, [loading, error, detail, messages.length]);

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
  }, [ticketId]);

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
    if (loading || error || !detail) return;
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
  }, [loading, error, detail, chatPanel, loadOlderMessages, loadOlderComments]);

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
    if (loading || error || !detail) return;
    void pollReadReceipts();
    const id = window.setInterval(() => void pollReadReceipts(), READ_RECEIPTS_POLL_MS);
    return () => window.clearInterval(id);
  }, [loading, error, detail, pollReadReceipts]);

  useEffect(() => {
    if (loading || error || !detail || !isLkTicketSource(detail.source) || chatPanel !== "comments") return;
    const id = window.setInterval(() => void pollComments(), MSG_POLL_MS);
    return () => window.clearInterval(id);
  }, [loading, error, detail, chatPanel, pollComments]);

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

  function openClassify(action: ClassifyAction) {
    setClassifyAction(action);
    setClassifyOpen(true);
  }

  async function handleClassifyConfirm(payload: {
    categoryId: number;
    leaf: TicketCategoryLeaf;
    comment: string;
  }) {
    if (!detail) return;
    setClassifyConfirming(true);
    try {
      if (classifyAction === "close") {
        const next = await closeTicket(detail.id, {
          categoryId: payload.categoryId,
          comment: payload.comment || undefined,
        });
        setDetail(next);
        setClassifyOpen(false);
        setCommentEditingId(null);
        setCommentDraft("");
        setReplyTo(null);
        setEditingId(null);
        setToast({ message: "Тикет закрыт", variant: "success" });
        return;
      }
      const next = await transferTicketToEngineers(detail.id, {
        categoryId: payload.categoryId,
        comment: isLkTicketSource(detail.source) ? payload.comment || undefined : undefined,
      });
      setDetail(next);
      setClassifyOpen(false);
      setToast({ message: "Тикет передан инженерам", variant: "success" });
    } catch (e: unknown) {
      const fallback =
        classifyAction === "close" ? "Не удалось закрыть тикет" : "Не удалось передать тикет";
      setToast({
        message: e instanceof Error ? e.message : fallback,
        variant: "error",
      });
    } finally {
      setClassifyConfirming(false);
    }
  }

  async function handleReopenTicket() {
    if (!detail || reopenLoading || !detail.can_reopen) return;
    setReopenLoading(true);
    try {
      const next = await reopenTicket(detail.id);
      setDetail(next);
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
        void fetchTicketDetail(ticketId).then(setDetail).catch(() => {});
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
    const normalized: File[] = [];
    for (const f of arr) {
      if (f.type.startsWith("image/")) {
        normalized.push(await compressImageToWebp(f));
      } else {
        normalized.push(f);
      }
    }
    setUploads((prev) => [
      ...prev,
      ...normalized.map((file) => ({
        id: crypto.randomUUID(),
        file,
        previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
        status: "pending" as const,
        uploaded: 0,
        total: file.size,
        isImage: file.type.startsWith("image/"),
      })),
    ]);
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
    xhr.send(fd);
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
          <Link to="/tickets" className="tk-back-link">
            ← К тикетам
          </Link>
        </div>
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
  const chatMessages = messages.filter((m) => !m.is_initial);
  const isLkTicket = isLkTicketSource(detail.source);
  const isCommentsPanel = isLkTicket && chatPanel === "comments";
  const hideQuickReplies = !isLkTicket;
  const feedMessages = isCommentsPanel ? comments.map(commentToMessage) : chatMessages;
  const hasIntro = !isCommentsPanel && introBody.length > 0;
  const feedLoadingOlder = isCommentsPanel ? commentsLoadingOlder : loadingOlder;
  const online = Boolean(detail.user_id) ? Boolean(detail.subscriber_online) : false;

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

  return (
    <div className="tp on" id="tp-ticket" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div className="tk-ticket-shell">
        <div className="tbar">
          <button type="button" className="tbk" onClick={() => navigate("/tickets")}>
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
            {detail.is_open && detail.queue_line === "cs" ? (
              <button type="button" className="tb3" onClick={() => openClassify("esc")}>
                Инженерам
              </button>
            ) : null}
            {detail.is_open && detail.queue_line === "engineers" ? (
              <button
                type="button"
                className="tb3"
                disabled={takeBackLoading}
                onClick={() => void handleTakeBackToKs()}
              >
                {takeBackLoading ? "Возврат…" : "Взять в работу"}
              </button>
            ) : null}
            {detail.is_open ? (
              <button type="button" className="tb3 cls" onClick={() => openClassify("close")}>
                Завершить
              </button>
            ) : detail.can_reopen ? (
              <button
                type="button"
                className="tb3"
                disabled={reopenLoading}
                onClick={() => void handleReopenTicket()}
              >
                {reopenLoading ? "Открываю…" : "Переоткрыть"}
              </button>
            ) : null}
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
          <div className={`czone tk-chat-main${isCommentsPanel ? " tk-chat-main--comments" : ""}`}>
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
                  feedMessages.map((m) =>
                    m.side === "bot" ? (
                      <div key={m.id} className="msg bot">
                        <div className="mc2">
                          <div className="bbl bot">
                            <div className="tk-msg-label">{ticketAuthorLabel(m, subscriberChatName)}</div>
                            <MessageBody text={m.text} />
                            <AttachmentsBlock msg={m} onOpenImage={openImageViewer} />
                          </div>
                          <div className="mtm">{formatMsgTime(m.created_at_iso) || "—"}</div>
                        </div>
                      </div>
                    ) : (
                      <div
                        key={m.id}
                        data-msg-id={m.id}
                        className={`${ticketMsgRowClass(m.side)}${highlightId === m.id ? " tk-msg--highlight" : ""}`}
                        onContextMenu={(e) => handleFeedContextMenu(e, m)}
                      >
                        <div className={ticketMavClass(m.side)}>{ticketAvatarLetter(m, subscriberChatName)}</div>
                        <div className="mc2">
                          <div className={ticketBblClass(m.side)}>
                            <div className="tk-msg-label">
                              {isCommentsPanel
                                ? m.author_name || ticketAuthorLabel(m, subscriberChatName)
                                : ticketAuthorLabel(m, subscriberChatName)}
                            </div>
                            {!isCommentsPanel && m.reply_preview ? (
                              <TicketMessageReplyQuote preview={m.reply_preview} onJump={scrollToMessage} />
                            ) : null}
                            <MessageBody text={m.text} />
                            {!isCommentsPanel ? (
                              <AttachmentsBlock msg={m} onOpenImage={openImageViewer} />
                            ) : null}
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
                            {!isCommentsPanel ? (
                              <TicketDeliveryTicks
                                side={m.side}
                                recipientReadAtIso={m.recipient_read_at_iso}
                                readBy={m.read_by}
                              />
                            ) : null}
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
                  <div className="tk-no-reply">
                    {isCommentsPanel
                      ? "Тикет закрыт — служебные комментарии доступны только для просмотра"
                      : "Тикет закрыт — переписка доступна только для просмотра"}
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
                                  void enqueueFiles(e.target.files || []);
                                  e.currentTarget.value = "";
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
              <div className="tk-imgv__box" onClick={(e) => e.stopPropagation()}>
                <button type="button" className="tk-imgv__close" aria-label="Закрыть" onClick={() => setImgViewerOpen(false)}>
                  ×
                </button>
                <button
                  type="button"
                  className="tk-imgv__nav tk-imgv__nav--prev"
                  aria-label="Предыдущее"
                  onClick={() =>
                    setImgViewerIndex((i) => {
                      const newIdx = allImageUrls.length ? (i - 1 + allImageUrls.length) % allImageUrls.length : 0;
                      imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                      return newIdx;
                    })
                  }
                >
                  ‹
                </button>
                <img className="tk-imgv__img" src={allImageUrls[Math.min(imgViewerIndex, allImageUrls.length - 1)]} alt="Просмотр" />
                <button
                  type="button"
                  className="tk-imgv__nav tk-imgv__nav--next"
                  aria-label="Следующее"
                  onClick={() =>
                    setImgViewerIndex((i) => {
                      const newIdx = allImageUrls.length ? (i + 1) % allImageUrls.length : 0;
                      imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                      return newIdx;
                    })
                  }
                >
                  ›
                </button>
                <div className="tk-imgv__counter" aria-live="polite">
                  {imgViewerIndex + 1} / {allImageUrls.length}
                </div>
              </div>
            </div>
          ) : null}

          {contextMenu ? (
            <TicketMessageContextMenu
              x={contextMenu.x}
              y={contextMenu.y}
              message={contextMenu.msg}
              allowReply={!isCommentsPanel && detail.is_open}
              commentMode={isCommentsPanel && detail.is_open}
              readOnly={!detail.is_open}
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

          <aside className={`tk-sidebar ip${sideOpen ? "" : " closed"}`} aria-label="Информация о тикете">
            <div className="tk-sidebar__accent" aria-hidden />
            <div className="ips">
              <div className="ipb">
                <div className="ipl">Абонент</div>
                {detail.user_id == null ? (
                  <>
                    <div className="tk-side-unknown" role="status">
                      Не удалось определить абонента
                    </div>
                    {detail.caller_name ? (
                      <div className="tk-side-meta">Как представился: {detail.caller_name}</div>
                    ) : null}
                    <button type="button" className="tb3 tk-link-subscriber-btn" onClick={() => setLinkSubscriberOpen(true)}>
                      Найти абонента
                    </button>
                  </>
                ) : (
                  <>
                    <div
                      className={
                        detail.subscriber_is_juridical === 2 ? "tk-side-name tk-side-name--jur" : "tk-side-name"
                      }
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
                      {subscriberSidebarName}
                    </div>
                    <div className="tk-side-meta">ID: {detail.user_id}</div>
                    {detail.subscriber_login ? (
                      <div className="tk-side-meta">Логин: {detail.subscriber_login}</div>
                    ) : null}
                    {detail.subscriber_profile_user_id != null ? (
                      <Link to={`/users/${detail.subscriber_profile_user_id}`} className="tk-profile-link">
                        Карточка абонента →
                      </Link>
                    ) : null}
                  </>
                )}
              </div>

              {detail.is_open && detail.subscriber_account && detail.user_id != null ? (
                <TicketSubscriberAccountSidebar
                  account={detail.subscriber_account}
                  isJuridical={detail.subscriber_is_juridical}
                />
              ) : null}

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
                      className={`ch-line ch-line--${queueLineBadgeClass(detail.queue_line)}`}
                    >
                      {queueLineShortLabel(detail.queue_line, detail.support_line)}
                    </span>
                  </span>
                </div>
                {detail.category_name || detail.category_parent_name ? (
                  <div className="kv tk-category-kv">
                    <div className="tk-category-kv__top">
                      <span className="kvk">Категория</span>
                      <span className="kvv">
                        {detail.category_parent_name || detail.category_name}
                      </span>
                    </div>
                    {detail.category_parent_name && detail.category_name ? (
                      <div className="tk-category-kv__child">{detail.category_name}</div>
                    ) : null}
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
        key={`${detail.id}-${classifyAction}`}
        open={classifyOpen}
        ticketId={detail.id}
        ticketSource={detail.source}
        initialCategoryId={detail.category_id}
        initialCategoryParentId={detail.category_parent_id}
        action={classifyAction}
        confirming={classifyConfirming}
        onClose={() => {
          if (!classifyConfirming) setClassifyOpen(false);
        }}
        onConfirm={handleClassifyConfirm}
      />

      <TicketLinkSubscriberModal
        open={linkSubscriberOpen}
        ticketId={detail.id}
        onClose={() => setLinkSubscriberOpen(false)}
        onLinked={(next) => {
          setDetail(next);
          setToast({ message: "Абонент привязан к тикету", variant: "success" });
        }}
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
