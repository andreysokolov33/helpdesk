import { memo, startTransition, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import UniversalSearch from "@/components/UniversalSearch";
import {
  COMMUNICATION_LABELS,
  mergeTrackerListPage,
  ticketListStatusColumn,
  trackerApiRowToTicketRow,
  type TrackerTicketListItem,
} from "@/api/tracker";
import {
  fetchHomeDashboard,
  fetchHomeDashboardDigest,
  fetchHomeTickets,
  fetchHomeTicketsDigest,
  type HomeRatingItem,
  type HomeTicketsResponse,
} from "@/api/home";
import { formatTicketListDate, formatWorkDurationSince } from "@/utils/ticketFormat";
import { ratingToneClass } from "@/utils/ratingTone";
import { TICKETS_LIST_POLL_JITTER_MS, TICKETS_LIST_POLL_MS } from "@/utils/ticketsListPoll";

const REPLY_SLA_MINUTES = 30;

function sameTicketListOrder(a: TrackerTicketListItem[], b: TrackerTicketListItem[]): boolean {
  if (a.length !== b.length) return false;
  return a.every((row, i) => row === b[i]);
}

function sameRatings(a: HomeRatingItem[], b: HomeRatingItem[]): boolean {
  if (a.length !== b.length) return false;
  return a.every(
    (r, i) =>
      b[i].ticket_id === r.ticket_id &&
      b[i].rating === r.rating &&
      b[i].rated_at === r.rated_at &&
      b[i].rating_comment === r.rating_comment &&
      b[i].subscriber_name === r.subscriber_name,
  );
}

function formatWaitLabel(row: TrackerTicketListItem, nowMs: number): { label: string; overdue: boolean } {
  const since = row.action_since || row.updated_at || row.date_of_create;
  const start = new Date(since).getTime();
  if (Number.isNaN(start)) return { label: "—", overdue: false };
  const min = Math.max(0, Math.floor((nowMs - start) / 60_000));
  const overdue = min >= REPLY_SLA_MINUTES;
  if (min < 60) return { label: `${min} мин`, overdue };
  const h = Math.floor(min / 60);
  const m = min % 60;
  return { label: m > 0 ? `${h} ч ${m} мин` : `${h} ч`, overdue };
}

function formatRatingDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

const HomeUrgentCard = memo(function HomeUrgentCard({
  row,
  nowMs,
  entering,
  onOpen,
}: {
  row: TrackerTicketListItem;
  nowMs: number;
  entering: boolean;
  onOpen: (id: number) => void;
}) {
  const wait = formatWaitLabel(row, nowMs);
  const name =
    row.subscriber_name ||
    row.subscriber_login ||
    (row.user_id != null ? `Абонент #${row.user_id}` : `Тикет #${row.id}`);
  return (
    <button
      type="button"
      className={`ug${entering ? " home-ug--enter" : ""}`}
      onClick={() => onOpen(row.id)}
    >
      <div className="home-urgent-meta">
        <span className="tag tn home-urgent-status">{COMMUNICATION_LABELS.needs_reply}</span>
        <span className="home-urgent-wait">
          <span className="pulse" /> {wait.label}
        </span>
        {wait.overdue ? (
          <span className="tag thi home-urgent-overdue">Превышено</span>
        ) : (
          <span className="home-urgent-overdue home-urgent-overdue--placeholder" aria-hidden>
            Превышено
          </span>
        )}
      </div>
      <div className="home-urgent-name">{name}</div>
      <div className="home-urgent-topic">{row.title}</div>
      <div className="home-urgent-duration" title="Время в работе">
        {formatWorkDurationSince(row.date_of_create, nowMs)}
      </div>
      <div className="home-reply-cta">Ответить →</div>
    </button>
  );
});

const HomeOpenTicketRow = memo(function HomeOpenTicketRow({
  row,
  nowMs,
  entering,
  onOpen,
}: {
  row: TrackerTicketListItem;
  nowMs: number;
  entering: boolean;
  onOpen: (id: number) => void;
}) {
  const t = trackerApiRowToTicketRow(row);
  const statusCol = ticketListStatusColumn(row);
  const workDuration = formatWorkDurationSince(row.date_of_create, nowMs);
  const updatedLabel = formatTicketListDate(row.updated_at || row.date_of_create);

  return (
    <tr
      className={`home-open-row${entering ? " home-open-row--enter" : ""}`}
      tabIndex={0}
      onClick={() => onOpen(row.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen(row.id);
        }
      }}
    >
      <td className="home-open-cell home-open-cell--id">
        <span className="home-open-id-wrap">
          <span
            className={`home-open-dot${t.dot === "red" ? " home-list-dot--alert" : t.dot === "wn" ? " home-list-dot--warn" : ""}`}
            style={t.dot === "i2" ? { background: "var(--i2)" } : undefined}
            aria-hidden
          />
          <span className="home-open-id">#{row.id}</span>
        </span>
      </td>
      <td className="home-open-cell home-open-cell--name">
        <strong>{t.name}</strong>
      </td>
      <td className="home-open-cell home-open-cell--topic">{t.topic}</td>
      <td className="home-open-cell home-open-cell--status">
        {statusCol.kind === "comm" ? (
          <span className={`ch-comm ch-comm--${statusCol.state}`} title={statusCol.label}>
            {statusCol.label}
          </span>
        ) : (
          <span className={`ch-status ch-status--${statusCol.status}`} title={statusCol.label}>
            {statusCol.label}
          </span>
        )}
      </td>
      <td className="home-open-cell home-open-cell--duration">{workDuration}</td>
      <td className="home-open-cell home-open-cell--updated">{updatedLabel}</td>
    </tr>
  );
});

function HomeOpenTicketsTable({
  rows,
  nowMs,
  enteringTicketIds,
  onOpen,
}: {
  rows: TrackerTicketListItem[];
  nowMs: number;
  enteringTicketIds: ReadonlySet<number>;
  onOpen: (id: number) => void;
}) {
  return (
    <div className="card home-open-card">
      <table className="dt home-open-table">
        <thead>
          <tr>
            <th>№</th>
            <th>Абонент</th>
            <th>Тема</th>
            <th>Статус</th>
            <th>В работе</th>
            <th>Обновлён</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <HomeOpenTicketRow
              key={row.id}
              row={row}
              nowMs={nowMs}
              entering={enteringTicketIds.has(row.id)}
              onOpen={onOpen}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HomeTab() {
  const navigate = useNavigate();
  const location = useLocation();
  const isHomeActive = location.pathname === "/";

  const [needsReplyRows, setNeedsReplyRows] = useState<TrackerTicketListItem[]>([]);
  const [openRows, setOpenRows] = useState<TrackerTicketListItem[]>([]);
  const [ticketTotal, setTicketTotal] = useState(0);
  const [needsReplyCount, setNeedsReplyCount] = useState(0);
  const [ratings, setRatings] = useState<HomeRatingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [nowPulse, setNowPulse] = useState(() => Date.now());
  const [enteringTicketIds, setEnteringTicketIds] = useState<ReadonlySet<number>>(() => new Set());

  const ticketsDigestRef = useRef<string | null>(null);
  const ratingsDigestRef = useRef<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const loadGenRef = useRef(0);
  const ticketIdsRef = useRef<Set<number>>(new Set());

  const applyHomeTickets = useCallback((data: HomeTicketsResponse, silent: boolean) => {
    const apply = () => {
      setNeedsReplyRows((prev) => {
        const merged = silent ? mergeTrackerListPage(prev, data.needs_reply) : data.needs_reply;
        return sameTicketListOrder(prev, merged) ? prev : merged;
      });
      setOpenRows((prev) => {
        const merged = silent ? mergeTrackerListPage(prev, data.open) : data.open;
        return sameTicketListOrder(prev, merged) ? prev : merged;
      });
      setTicketTotal((prev) => (prev !== data.total_open ? data.total_open : prev));
      setNeedsReplyCount((prev) => (prev !== data.needs_reply_count ? data.needs_reply_count : prev));

      const allIds = [...data.needs_reply, ...data.open].map((r) => r.id);
      if (silent) {
        const prevIds = ticketIdsRef.current;
        const newIds = allIds.filter((id) => !prevIds.has(id));
        ticketIdsRef.current = new Set(allIds);
        if (newIds.length > 0) {
          setEnteringTicketIds(new Set(newIds));
          window.setTimeout(() => setEnteringTicketIds(new Set()), 320);
        }
      } else {
        ticketIdsRef.current = new Set(allIds);
        setEnteringTicketIds(new Set());
      }
    };
    if (silent) startTransition(apply);
    else apply();
  }, []);

  const loadTickets = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent === true;
    const gen = ++loadGenRef.current;
    if (!silent) setLoading(true);
    try {
      const data = await fetchHomeTickets();
      if (gen !== loadGenRef.current) return;
      applyHomeTickets(data, silent);
      try {
        const dig = await fetchHomeTicketsDigest();
        if (gen === loadGenRef.current) ticketsDigestRef.current = dig.digest;
      } catch {
        /* digest необязателен */
      }
    } finally {
      if (gen === loadGenRef.current && !silent) setLoading(false);
    }
  }, [applyHomeTickets]);

  const loadRatings = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent === true;
    const data = await fetchHomeDashboard();
    const apply = () => {
      setRatings((prev) => (sameRatings(prev, data.ratings) ? prev : data.ratings));
    };
    if (silent) startTransition(apply);
    else apply();
    try {
      const dig = await fetchHomeDashboardDigest();
      ratingsDigestRef.current = dig.digest;
    } catch {
      /* digest необязателен */
    }
  }, []);

  const loadAll = useCallback(
    async (opts?: { silent?: boolean }) => {
      const silent = opts?.silent === true;
      await Promise.all([loadTickets({ silent }), loadRatings({ silent })]);
    },
    [loadTickets, loadRatings],
  );

  useEffect(() => {
    if (!isHomeActive) return;
    void loadAll();
  }, [isHomeActive, loadAll]);

  useEffect(() => {
    if (!isHomeActive) return;
    const id = window.setInterval(() => setNowPulse(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, [isHomeActive]);

  const pollHome = useCallback(async () => {
    if (!isHomeActive || document.visibilityState === "hidden") return;
    try {
      const [ticketsDig, ratingsDig] = await Promise.all([
        fetchHomeTicketsDigest({
          digest: ticketsDigestRef.current ?? undefined,
        }),
        fetchHomeDashboardDigest({
          digest: ratingsDigestRef.current ?? undefined,
        }),
      ]);
      ticketsDigestRef.current = ticketsDig.digest;
      ratingsDigestRef.current = ratingsDig.digest;

      const tasks: Promise<void>[] = [];
      if (ticketsDig.changed) {
        tasks.push(loadTickets({ silent: true }));
      } else {
        setTicketTotal((prev) => (prev !== ticketsDig.total_open ? ticketsDig.total_open : prev));
        setNeedsReplyCount((prev) =>
          prev !== ticketsDig.needs_reply_count ? ticketsDig.needs_reply_count : prev,
        );
      }
      if (ratingsDig.changed) {
        tasks.push(loadRatings({ silent: true }));
      }
      if (tasks.length > 0) await Promise.all(tasks);
    } catch {
      await loadAll({ silent: true });
    }
  }, [isHomeActive, loadTickets, loadRatings, loadAll]);

  useEffect(() => {
    if (!isHomeActive) return;

    const schedule = () => {
      const jitter = Math.floor(Math.random() * TICKETS_LIST_POLL_JITTER_MS);
      pollTimerRef.current = window.setTimeout(() => {
        void pollHome().finally(schedule);
      }, TICKETS_LIST_POLL_MS + jitter);
    };

    const onVisible = () => {
      if (document.visibilityState === "visible" && isHomeActive) void pollHome();
    };

    schedule();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      if (pollTimerRef.current != null) window.clearTimeout(pollTimerRef.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [isHomeActive, pollHome]);

  const openTicket = useCallback((id: number) => navigate(`/tickets/${id}`), [navigate]);

  const showNeedsReply = !loading && needsReplyRows.length > 0;
  const showOpen = !loading && openRows.length > 0;
  const urgentGridClass =
    needsReplyRows.length >= 3
      ? "home-urgent-grid--n3"
      : needsReplyRows.length === 2
        ? "home-urgent-grid--n2"
        : "home-urgent-grid--n1";

  return (
    <div className="tp on home-page">
      <div className="pg">
        <div style={{ textAlign: "center", padding: "8px 0 4px" }}>
          <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 14, color: "var(--ink)" }}>
            Найдите <span className="home-accent">абонента</span> или ответ в{" "}
            <span className="home-accent">базе знаний</span>
          </div>
          <UniversalSearch />
        </div>

        {!loading && ticketTotal > 0 ? (
          <p style={{ fontSize: 12, color: "var(--i2)", textAlign: "center", marginTop: 8 }}>
            {ticketTotal === 1 ? (
              <>
                <strong style={{ color: "var(--ink)" }}>1 заявка</strong>
                {needsReplyCount > 0 ? (
                  <>
                    {" "}
                    — <span className="home-stat-alert">ждёт ответа</span>
                  </>
                ) : null}
              </>
            ) : (
              <>
                <strong style={{ color: "var(--ink)" }}>{ticketTotal} заявок</strong>
                {needsReplyCount > 0 ? (
                  <>
                    {" "}
                    —{" "}
                    <span className="home-stat-alert">
                      {needsReplyCount} ждут ответа
                    </span>
                  </>
                ) : null}
              </>
            )}
          </p>
        ) : null}

        {loading ? (
          <div className="home-loading-hint">Загрузка тикетов…</div>
        ) : null}

        {showNeedsReply ? (
          <div>
            <div className="home-section-label">Ждут ответа</div>
            <div className={`home-urgent-grid ${urgentGridClass}`}>
              {needsReplyRows.map((row) => (
                <HomeUrgentCard
                  key={row.id}
                  row={row}
                  nowMs={nowPulse}
                  entering={enteringTicketIds.has(row.id)}
                  onOpen={openTicket}
                />
              ))}
            </div>
          </div>
        ) : null}

        {showOpen ? (
          <div>
            <div className="home-section-label">Открытые заявки</div>
            <HomeOpenTicketsTable
              rows={openRows}
              nowMs={nowPulse}
              enteringTicketIds={enteringTicketIds}
              onOpen={openTicket}
            />
          </div>
        ) : null}

        {!loading && ratings.length > 0 ? (
          <div className="card">
            <div className="ct">Последние оценки</div>
            <table className="dt">
              <thead>
                <tr>
                  <th>Клиент</th>
                  <th>Комментарий</th>
                  <th>Оценка</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {ratings.map((r) => (
                  <tr
                    key={`${r.ticket_id}-${r.rated_at ?? ""}`}
                    className="home-rating-row"
                    tabIndex={0}
                    onClick={() => openTicket(r.ticket_id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openTicket(r.ticket_id);
                      }
                    }}
                  >
                    <td>
                      <strong>{r.subscriber_name}</strong>
                    </td>
                    <td style={{ color: "var(--i2)" }}>{r.rating_comment || "—"}</td>
                    <td>
                      <span
                        className={`rating-tone rating-tone--pill ${ratingToneClass(r.rating, true)}`.trim()}
                      >
                        {r.rating}
                      </span>
                    </td>
                    <td style={{ color: "var(--i3)" }}>{formatRatingDate(r.rated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        <p
          className="home-contact"
          data-tip="Любые пожелания, идеи и рекомендации по улучшению интерфейса писать на эту почту."
        >
          По всем вопросам и предложениям:{" "}
          <a className="home-contact__mail" href="mailto:os@wifitochka.ru">
            os@wifitochka.ru
          </a>
        </p>
      </div>
    </div>
  );
}
