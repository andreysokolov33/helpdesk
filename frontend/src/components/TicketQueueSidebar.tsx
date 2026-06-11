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

function queueBadgeMod(row: TrackerTicketListItem): "new" | "work" | "wait" | "comm" {
  const statusCol = ticketListStatusColumn(row);
  if (statusCol.kind === "comm") return "comm";
  if (row.status === "pending" || row.status === "open") return "new";
  if (row.status === "in_progress") return "work";
  return "wait";
}

type Props = {
  activeTicketId: number;
};

export default function TicketQueueSidebar({ activeTicketId }: Props) {
  const navigate = useNavigate();
  const [rows, setRows] = useState<TrackerTicketListItem[]>([]);
  const [total, setTotal] = useState(0);
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
        setTotal(data.total);
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
      else setTotal((prev) => (prev !== dig.total ? dig.total : prev));
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
        <span className="tk-cc-queue__count" title={polling ? "Обновление…" : undefined}>
          {total > 99 ? "99+" : total}
        </span>
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
          const preview = row.title?.trim() || "Без темы";
          const timeIso = row.updated_at || row.date_of_create;
          const badgeLabel =
            badgeMod === "comm"
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
                <span className="tk-cc-queue__item-name">{displayName(row)}</span>
                <span className="tk-cc-queue__item-time">{formatQueueRelativeTime(timeIso)}</span>
              </div>
              <div className="tk-cc-queue__item-preview">{preview}</div>
              <span className={`tk-cc-queue__badge tk-cc-queue__badge--${badgeMod}`}>
                {badgeLabel}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
