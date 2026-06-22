import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import MessageBody from "@/components/MessageBody";
import TicketMessageAttachments, { collectMessageImageUrls } from "@/components/TicketMessageAttachments";
import {
  fetchMessageContext,
  formatMsgTime,
  type TicketMessage,
  type TicketMessageContext,
} from "@/api/ticket";
import { isEngineerTicketMessage, ticketAuthorLabel } from "@/utils/ticketMessages";

type Props = {
  open: boolean;
  messageId: number;
  currentTicketId: number;
  subscriberName?: string;
  onClose: () => void;
};

export default function TicketCrossTicketMessageModal({
  open,
  messageId,
  currentTicketId,
  subscriberName = "Абонент",
  onClose,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const imgViewerUrlRef = useRef<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ctx, setCtx] = useState<TicketMessageContext | null>(null);
  const [imgViewerOpen, setImgViewerOpen] = useState(false);
  const [imgViewerIndex, setImgViewerIndex] = useState(0);

  const allImageUrls = useMemo(() => collectMessageImageUrls(ctx?.messages ?? []), [ctx?.messages]);

  const openImageViewer = useCallback(
    (url: string) => {
      const idx = allImageUrls.indexOf(url);
      imgViewerUrlRef.current = url;
      setImgViewerIndex(idx >= 0 ? idx : 0);
      setImgViewerOpen(true);
    },
    [allImageUrls],
  );

  useEffect(() => {
    if (!open || messageId <= 0) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setCtx(null);
    setImgViewerOpen(false);
    void fetchMessageContext(messageId)
      .then((data) => {
        if (!cancelled) setCtx(data);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Не удалось загрузить сообщение");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, messageId]);

  useLayoutEffect(() => {
    if (!open || !ctx || loading) return;
    const el = scrollRef.current?.querySelector(`[data-msg-id="${ctx.focus_message_id}"]`);
    el?.scrollIntoView({ block: "center" });
  }, [open, ctx, loading]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (imgViewerOpen) {
          e.preventDefault();
          setImgViewerOpen(false);
          return;
        }
        onClose();
      }
      if (!imgViewerOpen || !allImageUrls.length) return;
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setImgViewerIndex((i) => {
          const newIdx = (i - 1 + allImageUrls.length) % allImageUrls.length;
          imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
          return newIdx;
        });
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setImgViewerIndex((i) => {
          const newIdx = (i + 1) % allImageUrls.length;
          imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
          return newIdx;
        });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, imgViewerOpen, allImageUrls]);

  if (!open) return null;

  function renderMessage(m: TicketMessage, focusId: number) {
    if (m.side === "bot") {
      return (
        <div
          key={m.id}
          data-msg-id={m.id}
          className={`tk-xref-msg tk-xref-msg--bot${m.id === focusId ? " tk-xref-msg--focus" : ""}`}
        >
          <div className="tk-xref-msg__meta">
            {ticketAuthorLabel(m, subscriberName)} · {formatMsgTime(m.created_at_iso) || "—"}
          </div>
          <div className="tk-xref-msg__body">
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
        className={`tk-xref-msg${outgoing ? " tk-xref-msg--out" : " tk-xref-msg--in"}${engineer ? " tk-xref-msg--engineer" : ""}${m.id === focusId ? " tk-xref-msg--focus" : ""}`}
      >
        <div className="tk-xref-msg__meta">
          {outgoing ? "Вы" : ticketAuthorLabel(m, subscriberName)} · {formatMsgTime(m.created_at_iso) || "—"}
        </div>
        <div className="tk-xref-msg__body">
          <MessageBody text={m.text} />
          <TicketMessageAttachments msg={m} onOpenImage={openImageViewer} />
        </div>
      </div>
    );
  }

  const ticketId = ctx?.ticket_id ?? null;
  const hasTicket = ticketId != null && ticketId > 0;
  const isForeign = hasTicket && ticketId !== currentTicketId;

  const title = hasTicket ? "Сообщение из другого тикета" : "Контекст сообщения";
  const subtitle = hasTicket ? (
    <>
      Цитата относится к тикету <span className="tk-xref-modal__ticket">#{ticketId}</span>
      {ctx?.ticket_title ? (
        <span className="tk-xref-modal__title" title={ctx.ticket_title}>
          {" "}
          · {ctx.ticket_title}
        </span>
      ) : null}
    </>
  ) : (
    <>Сообщение из переписки без привязки к тикету</>
  );

  return (
    <>
      <div
        className="clf-mo open"
        role="dialog"
        aria-modal="true"
        aria-labelledby="tk-xref-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="clf-box tk-xref-modal">
          <div className="tk-xref-modal__head">
            <div className="tk-xref-modal__head-text">
              <div className="clf-hd-t" id="tk-xref-title">
                {title}
              </div>
              {ctx ? <div className="tk-xref-modal__sub">{subtitle}</div> : <div className="tk-xref-modal__sub">Загрузка…</div>}
            </div>
            <button type="button" className="tk-xref-modal__close" onClick={onClose} aria-label="Закрыть">
              ×
            </button>
          </div>

          {isForeign && ticketId ? (
            <div className="tk-xref-modal__banner">
              <span className="tk-xref-modal__banner-text">
                Это сообщение из тикета #{ticketId}
                {!ctx?.ticket_is_open ? " (закрыт)" : ""}
              </span>
              <Link to={`/tickets/${ticketId}`} className="tk-xref-modal__go" onClick={onClose}>
                Перейти в тикет
              </Link>
            </div>
          ) : null}

          <div className={`tk-xref-modal__body${hasTicket ? "" : " tk-xref-modal__body--orphan"}`} ref={scrollRef}>
            {loading ? <div className="tk-xref-modal__state">Загрузка сообщений…</div> : null}
            {error ? (
              <div className="tk-xref-modal__state tk-xref-modal__state--error" role="alert">
                {error}
              </div>
            ) : null}
            {!loading && !error && ctx ? (
              <>
                {ctx.has_older ? <div className="tk-xref-modal__edge">··· более ранние сообщения ···</div> : null}
                <div className="tk-xref-modal__feed">
                  {ctx.messages.map((m) => renderMessage(m, ctx.focus_message_id))}
                </div>
                {ctx.has_newer ? <div className="tk-xref-modal__edge">··· более поздние сообщения ···</div> : null}
              </>
            ) : null}
          </div>

          <div className="clf-ft tk-xref-modal__ft">
            <button type="button" className="clf-btn sec" onClick={onClose}>
              Закрыть
            </button>
            {isForeign && ticketId ? (
              <Link to={`/tickets/${ticketId}`} className="clf-btn pri tk-xref-modal__go-ft" onClick={onClose}>
                Открыть тикет #{ticketId}
              </Link>
            ) : null}
          </div>
        </div>
      </div>

      {imgViewerOpen && allImageUrls.length ? (
        <div className="tk-imgv" role="dialog" aria-modal="true" onClick={() => setImgViewerOpen(false)}>
          <button type="button" className="tk-imgv__close" aria-label="Закрыть" onClick={() => setImgViewerOpen(false)}>
            ×
          </button>
          {allImageUrls.length > 1 ? (
            <button
              type="button"
              className="tk-imgv__nav tk-imgv__nav--prev"
              aria-label="Предыдущее"
              onClick={(e) => {
                e.stopPropagation();
                setImgViewerIndex((i) => {
                  const newIdx = (i - 1 + allImageUrls.length) % allImageUrls.length;
                  imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                  return newIdx;
                });
              }}
            >
              ‹
            </button>
          ) : null}
          <div className="tk-imgv__box" onClick={(e) => e.stopPropagation()}>
            <img
              className="tk-imgv__img"
              src={allImageUrls[Math.min(imgViewerIndex, allImageUrls.length - 1)]}
              alt="Просмотр"
            />
            {allImageUrls.length > 1 ? (
              <div className="tk-imgv__counter" aria-live="polite">
                {imgViewerIndex + 1} / {allImageUrls.length}
              </div>
            ) : null}
          </div>
          {allImageUrls.length > 1 ? (
            <button
              type="button"
              className="tk-imgv__nav tk-imgv__nav--next"
              aria-label="Следующее"
              onClick={(e) => {
                e.stopPropagation();
                setImgViewerIndex((i) => {
                  const newIdx = (i + 1) % allImageUrls.length;
                  imgViewerUrlRef.current = allImageUrls[newIdx] ?? imgViewerUrlRef.current;
                  return newIdx;
                });
              }}
            >
              ›
            </button>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
