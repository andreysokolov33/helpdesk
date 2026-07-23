import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchAuthMe } from "@/api/auth";
import {
  fetchOpenTrackerTickets,
  fetchTrackerListDigest,
  mergeTrackerListPage,
  ticketListNeedsAttention,
  ticketListStatusColumn,
  type TrackerTicketListItem,
} from "@/api/tracker";
import { fetchUnreadTicketsCount } from "@/api/ticketsNav";
import CallCenterPhoneIcon from "@/components/CallCenterPhoneIcon";
import TopSubscriberBadge from "@/components/TopSubscriberBadge";
import { isCallCenterTicketSource } from "@/utils/ticketLabels";
import { loadTicketsPerPage, type TicketsListPerPage } from "@/utils/ticketsListPrefs";

const POLL_MS = 12_000;
const POLL_JITTER_MS = 6_000;

function formatQueueRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const diffMin = Math.floor((Date.now() - t) / 60_000);
  if (diffMin < 1) return "сейчас";
  if (diffMin < 60) return `${diffMin} мин`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH} ч`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD} д`;
}

function queuePreviewText(row: TrackerTicketListItem): string {
  const last = row.last_message_text?.trim();
  if (last) return last;
  return row.title?.trim() || "Без темы";
}

function queueBadgeMod(row: TrackerTicketListItem): "new" | "work" | "wait" | "comm" | "awaiting" {
  const statusCol = ticketListStatusColumn(row);
  if (statusCol.kind === "comm") {
    return statusCol.state === "needs_reply" ? "comm" : "awaiting";
  }
  if (row.status === "pending" || row.status === "open") return "new";
  if (row.status === "in_progress") return "work";
  return "wait";
}

type Props = {
  activeTicketId: number;
  /** Мгновенная синхронизация статуса открытого тикета из поллинга чата. */
  activeTicketSync?: ActiveTicketQueueSync | null;
  /** Триггер тихого обновления списка (новые сообщения / смена очереди). */
  refreshNonce?: number;
  onTicketSelect?: () => void;
  onClose?: () => void;
};

export type ActiveTicketQueueSync = {
  id: number;
  status: string;
  status_label: string;
  queue_line: string;
  queue_line_label?: string;
  action_by: string;
  chat_turn: string;
  action_since?: string | null;
  list_highlight: string;
  communication_state?: string | null;
  communication_label?: string | null;
  updated_at?: string | null;
  /** Последнее сообщение открытого тикета (мгновенное обновление превью). */
  last_message_text?: string | null;
};

function patchRowFromSync(
  row: TrackerTicketListItem,
  sync: ActiveTicketQueueSync,
): TrackerTicketListItem {
  return {
    ...row,
    status: sync.status,
    status_label: sync.status_label,
    queue_line: sync.queue_line as TrackerTicketListItem["queue_line"],
    support_line_label: sync.queue_line_label || row.support_line_label,
    action_by: sync.action_by as TrackerTicketListItem["action_by"],
    chat_turn: sync.chat_turn as TrackerTicketListItem["chat_turn"],
    action_since: sync.action_since ?? row.action_since,
    list_highlight: sync.list_highlight as TrackerTicketListItem["list_highlight"],
    communication_state:
      (sync.communication_state as TrackerTicketListItem["communication_state"]) ??
      row.communication_state,
    communication_label: sync.communication_label ?? row.communication_label,
    updated_at: sync.updated_at ?? row.updated_at,
    last_message_text:
      sync.last_message_text !== undefined ? sync.last_message_text : row.last_message_text,
  };
}

export default function TicketQueueSidebar({
  activeTicketId,
  activeTicketSync = null,
  refreshNonce = 0,
  onTicketSelect,
  onClose,
}: Props) {
  const navigate = useNavigate();
  const [rows, setRows] = useState<TrackerTicketListItem[]>([]);
  const [needsReplyCount, setNeedsReplyCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [prefsReady, setPrefsReady] = useState(false);
  const [perPage, setPerPage] = useState<TicketsListPerPage>(20);
  const viewerIdRef = useRef<number | null>(null);
  const loadGenRef = useRef(0);
  const digestRef = useRef<string | null>(null);
  const rowIdsRef = useRef<Set<number>>(new Set());
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((me) => {
        if (cancelled) return;
        viewerIdRef.current = me.user_id;
        setPerPage(loadTicketsPerPage(me.user_id));
        setPrefsReady(true);
      })
      .catch(() => {
        if (!cancelled) setPrefsReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const sortedRows = useMemo(() => {
    const urgent: TrackerTicketListItem[] = [];
    const rest: TrackerTicketListItem[] = [];
    for (const row of rows) {
      if (ticketListNeedsAttention(row)) urgent.push(row);
      else rest.push(row);
    }
    return [...urgent, ...rest];
  }, [rows]);

  const loadList = useCallback(
    async (opts?: { silent?: boolean }) => {
      if (!prefsReady) return;
      const silent = opts?.silent === true;
      const gen = ++loadGenRef.current;
      if (!silent) {
        setLoading(true);
      } else {
        setPolling(true);
      }
      try {
        const data = await fetchOpenTrackerTickets({ page: 1, per_page: perPage });
        if (gen !== loadGenRef.current) return;
        const apply = (items: TrackerTicketListItem[]) => {
          if (silent) {
            const prevIds = rowIdsRef.current;
            const newIds = items.filter((r) => !prevIds.has(r.id)).map((r) => r.id);
            rowIdsRef.current = new Set(items.map((r) => r.id));
            startTransition(() => {
              setRows((prev) => mergeTrackerListPage(prev, items));
              void newIds;
            });
          } else {
            rowIdsRef.current = new Set(items.map((r) => r.id));
            setRows(items);
          }
        };
        apply(data.items);
        try {
          const unread = await fetchUnreadTicketsCount();
          if (gen === loadGenRef.current) setNeedsReplyCount(unread);
        } catch {
          /* keep previous */
        }
        try {
          const dig = await fetchTrackerListDigest({ page: 1, per_page: perPage });
          if (gen === loadGenRef.current) digestRef.current = dig.digest;
        } catch {
          /* optional */
        }
      } finally {
        if (gen !== loadGenRef.current) return;
        if (!silent) setLoading(false);
        else setPolling(false);
      }
    },
    [prefsReady, perPage],
  );

  useEffect(() => {
    if (!prefsReady) return;
    void loadList();
  }, [prefsReady, loadList]);

  useEffect(() => {
    if (!activeTicketSync || activeTicketSync.id !== activeTicketId) return;
    setRows((prev) => {
      const idx = prev.findIndex((r) => r.id === activeTicketSync.id);
      if (idx < 0) return prev;
      const oldRow = prev[idx];
      const nextRow = patchRowFromSync(oldRow, activeTicketSync);
      if (
        oldRow.status === nextRow.status &&
        oldRow.list_highlight === nextRow.list_highlight &&
        oldRow.action_by === nextRow.action_by &&
        oldRow.chat_turn === nextRow.chat_turn &&
        oldRow.queue_line === nextRow.queue_line &&
        oldRow.updated_at === nextRow.updated_at &&
        oldRow.last_message_text === nextRow.last_message_text
      ) {
        return prev;
      }
      const wasUrgent = ticketListNeedsAttention(oldRow);
      const nowUrgent = ticketListNeedsAttention(nextRow);
      if (wasUrgent !== nowUrgent) {
        queueMicrotask(() => {
          setNeedsReplyCount((c) => Math.max(0, c + (nowUrgent ? 1 : -1)));
        });
      }
      const next = prev.slice();
      next[idx] = nextRow;
      return next;
    });
  }, [activeTicketSync, activeTicketId]);

  useEffect(() => {
    if (!prefsReady || refreshNonce <= 0) return;
    const t = window.setTimeout(() => {
      void loadList({ silent: true });
    }, 80);
    return () => window.clearTimeout(t);
  }, [prefsReady, refreshNonce, loadList]);

  const pollList = useCallback(async () => {
    if (!prefsReady || document.visibilityState === "hidden") return;
    setPolling(true);
    try {
      const dig = await fetchTrackerListDigest({
        page: 1,
        per_page: perPage,
        digest: digestRef.current ?? undefined,
      });
      digestRef.current = dig.digest;
      if (dig.changed) await loadList({ silent: true });
      else {
        try {
          const unread = await fetchUnreadTicketsCount();
          setNeedsReplyCount(unread);
        } catch {
          /* keep previous */
        }
      }
    } catch {
      await loadList({ silent: true });
    } finally {
      setPolling(false);
    }
  }, [prefsReady, perPage, loadList]);

  useEffect(() => {
    if (!prefsReady) return;
    const schedule = () => {
      const jitter = Math.floor(Math.random() * POLL_JITTER_MS);
      pollTimerRef.current = window.setTimeout(() => {
        void pollList().finally(schedule);
      }, POLL_MS + jitter);
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") void pollList();
    };
    schedule();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      if (pollTimerRef.current != null) window.clearTimeout(pollTimerRef.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [prefsReady, pollList]);

  function openTicket(id: number) {
    onTicketSelect?.();
    if (id === activeTicketId) return;
    navigate(`/tickets/${id}`);
  }

  function displayName(row: TrackerTicketListItem): string {
    const name = row.subscriber_name?.trim();
    if (name) return name;
    if (row.subscriber_login?.trim()) return row.subscriber_login.trim();
    if (row.user_id != null) return `Абонент #${row.user_id}`;
    return `Тикет #${row.id}`;
  }

  return (
    <section className="tk-cc-queue" aria-label="Очередь тикетов">
      <div className="tk-cc-queue__head">
        <span className="tk-cc-queue__title">Очередь чатов</span>
        <div className="tk-cc-queue__head-actions">
          <span
            className="tk-cc-queue__count"
            title={polling ? "Обновление…" : "Тикеты, где нужен ответ"}
          >
            {needsReplyCount > 99 ? "99+" : needsReplyCount}
          </span>
          {onClose ? (
            <button
              type="button"
              className="tk-cc-drawer-close"
              onClick={onClose}
              aria-label="Закрыть очередь"
            >
              ×
            </button>
          ) : null}
        </div>
      </div>
      <div className="tk-cc-queue__scroll">
        {loading && rows.length === 0 ? (
          <div className="tk-cc-queue__hint">Загрузка…</div>
        ) : null}
        {!loading && sortedRows.length === 0 ? (
          <div className="tk-cc-queue__hint">Нет открытых тикетов</div>
        ) : null}
        {sortedRows.map((row) => {
          const statusCol = ticketListStatusColumn(row);
          const badgeMod = queueBadgeMod(row);
          const needsAttention = ticketListNeedsAttention(row);
          /** «Нужен ответ» — только бейдж, без красного фона всей строки. */
          const rowHighlight = needsAttention && badgeMod !== "comm";
          const preview = queuePreviewText(row);
          const timeIso = row.updated_at || row.date_of_create;
          const badgeLabel =
            badgeMod === "comm" || badgeMod === "awaiting"
              ? statusCol.label.toLowerCase()
              : badgeMod === "new"
                ? "новый"
                : statusCol.label.toLowerCase();
          return (
            <button
              key={row.id}
              type="button"
              className={`tk-cc-queue__item${row.id === activeTicketId ? " tk-cc-queue__item--active" : ""}${rowHighlight ? " tk-cc-queue__item--unread" : ""}`}
              onClick={() => openTicket(row.id)}
            >
              <div className="tk-cc-queue__item-top">
                <div className="tk-cc-queue__item-name-row">
                  {isCallCenterTicketSource(row.source) ? (
                    <span
                      className="ch-call-ico"
                      title="Зарегистрирован после звонка на горячую линию"
                    >
                      <CallCenterPhoneIcon />
                    </span>
                  ) : null}
                  <TopSubscriberBadge rank={row.top_subscriber_rank} />
                  {row.object_type === "user" && (row.subscriber_is_juridical ?? 0) === 2 ? (
                    <span className="ch-jur-mark" title="Юридическое лицо">
                      ЮЛ
                    </span>
                  ) : null}
                  <span className="tk-cc-queue__item-name">{displayName(row)}</span>
                </div>
                <span className="tk-cc-queue__item-time">{formatQueueRelativeTime(timeIso)}</span>
              </div>
              <div className="tk-cc-queue__item-bottom">
                <div className="tk-cc-queue__item-preview">{preview}</div>
                <span className={`tk-cc-queue__badge tk-cc-queue__badge--${badgeMod}`}>
                  {badgeLabel}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
