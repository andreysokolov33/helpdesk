import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { fetchAuthMe } from "@/api/auth";
import DatePickerField from "@/components/DatePickerField";
import {
  fetchOpenTrackerTickets,
  fetchTrackerListDigest,
  mergeTrackerListPage,
  ticketListAssigneePill,
  ticketListNeedsAttention,
  ticketListStatusColumn,
  type TrackerTicketListItem,
  type TrackerTicketListStats,
} from "@/api/tracker";
import {
  formatRatingAvg,
  formatTicketUpdatedLocal,
  formatWorkDurationBetween,
  formatWorkDurationSince,
  ratingToneClass,
} from "@/utils/ticketFormat";
import { queueLineBadgeClass, queueLineShortLabel } from "@/utils/ticketLabels";
import {
  TICKETS_LIST_PER_PAGE_OPTIONS,
  loadTicketsPerPage,
  saveTicketsPerPage,
  type TicketsListPerPage,
} from "@/utils/ticketsListPrefs";
import { MOCK_KB, MOCK_SUBSCRIBERS, MOCK_TICKETS_OPEN, MOCK_TICKETS_URGENT, type TicketRow } from "@/data/mockCc";

type ChatMsg = { id: string; side: "cl" | "ag" | "note"; text: string; time: string };

/** Базовый интервал поллинга + джиттер, чтобы 20 операторов не били в БД синхронно. */
const TICKETS_LIST_POLL_MS = 12_000;
const TICKETS_LIST_POLL_JITTER_MS = 6_000;

const initialMsgs: ChatMsg[] = [
  { id: "1", side: "cl", text: "Здравствуйте! Где посмотреть детализацию?", time: "14:03" },
  { id: "2", side: "ag", text: "Здравствуйте! Сейчас помогу", time: "14:05" },
];

function CallCenterPhoneIcon() {
  return (
    <svg className="ch-call-ico-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M6.5 4.5h3l2 4-2.5 1.5a11 11 0 005.5 5.5L15 13l4 2v3a2 2 0 01-2 2A15 15 0 014 6.5a2 2 0 012-2z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function RatingStars({ value }: { value: number | null }) {
  if (value == null) return <span className="ch-muted">—</span>;
  return (
    <span className="ch-rating" title={`Оценка: ${value}`}>
      <span className="ch-rating-num">{value}</span>
      <span className="ch-rating-stars" aria-hidden>
        {"★".repeat(value)}
        {"☆".repeat(Math.max(0, 5 - value))}
      </span>
    </span>
  );
}

export default function ChatsTab() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const idParam = Number(params.get("id")) || 0;
  const ALL: TicketRow[] = useMemo(() => [...MOCK_TICKETS_URGENT, ...MOCK_TICKETS_OPEN], []);

  const navState = location.state as { ticketRow?: TicketRow } | null;
  const stateTicket = navState?.ticketRow;

  const ticket = useMemo(() => {
    const fromMock = ALL.find((t) => t.id === idParam);
    if (fromMock) return fromMock;
    if (stateTicket && stateTicket.id === idParam) return stateTicket;
    if (idParam)
      return {
        id: idParam,
        name: "Тикет",
        topic: "Откройте тикет из списка — данные не загружены",
        status: "work",
        time: "—",
        dot: "i2",
      } as TicketRow;
    return ALL[0];
  }, [ALL, idParam, stateTicket]);
  const sub = useMemo(
    () => MOCK_SUBSCRIBERS.find((s) => ticket.name.includes(s.n.split(" ")[0])) ?? MOCK_SUBSCRIBERS[2],
    [ticket.name],
  );

  const hasId = Boolean(params.get("id"));
  const [listMode, setListMode] = useState(!hasId);

  useEffect(() => {
    setListMode(!params.get("id"));
  }, [params]);
  const [msgs, setMsgs] = useState<ChatMsg[]>(initialMsgs);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"r" | "n">("r");
  const [kbOpen, setKbOpen] = useState(false);
  const [kbFilter, setKbFilter] = useState("");
  const [sideOpen, setSideOpen] = useState(true);
  const [diagRun, setDiagRun] = useState(false);
  const [diagStep, setDiagStep] = useState("");

  const filteredKb = useMemo(() => {
    const q = kbFilter.trim().toLowerCase();
    if (!q) return MOCK_KB;
    return MOCK_KB.filter((k) => k.t.toLowerCase().includes(q) || k.k.includes(q));
  }, [kbFilter]);

  const [listRows, setListRows] = useState<TrackerTicketListItem[]>([]);
  const [listTotal, setListTotal] = useState(0);
  const [listStats, setListStats] = useState<TrackerTicketListStats | null>(null);
  const [listPage, setListPage] = useState(1);
  const [perPage, setPerPage] = useState<TicketsListPerPage>(20);
  const [listPrefsReady, setListPrefsReady] = useState(false);
  const viewerIdRef = useRef<number | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const [listPolling, setListPolling] = useState(false);
  const [listError, setListError] = useState("");
  const [nowPulse, setNowPulse] = useState(() => Date.now());
  const listLoadGenRef = useRef(0);
  const listDigestRef = useRef<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const listRowIdsRef = useRef<Set<number>>(new Set());
  const [enteringRowIds, setEnteringRowIds] = useState<ReadonlySet<number>>(() => new Set());

  const closedMode = params.get("closed") === "true";
  const dateFrom = params.get("date_from") ?? "";
  const dateTo = params.get("date_to") ?? "";
  const assignedToParam = params.get("assigned_to") ?? "";
  const assignedTo = assignedToParam && /^\d+$/.test(assignedToParam) ? Number(assignedToParam) : undefined;
  const periodFilterActive = Boolean(dateFrom && dateTo);
  const [subscriberInput, setSubscriberInput] = useState(() => params.get("subscriber_q") ?? "");
  const subscriberQ = params.get("subscriber_q") ?? "";

  useEffect(() => {
    setSubscriberInput(subscriberQ);
  }, [subscriberQ]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      const trimmed = subscriberInput.trim();
      if (trimmed === subscriberQ) return;
      const next = new URLSearchParams(params);
      if (trimmed) next.set("subscriber_q", trimmed);
      else next.delete("subscriber_q");
      next.delete("page");
      setParams(next, { replace: true });
      setListPage(1);
    }, 350);
    return () => window.clearTimeout(t);
  }, [subscriberInput, subscriberQ, params, setParams]);

  useEffect(() => {
    if (!listMode) return;
    const id = window.setInterval(() => setNowPulse(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, [listMode]);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((me) => {
        if (cancelled) return;
        viewerIdRef.current = me.user_id;
        setPerPage(loadTicketsPerPage(me.user_id));
        setListPrefsReady(true);
      })
      .catch(() => {
        if (!cancelled) setListPrefsReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadTicketsList = useCallback(
    async (opts?: { silent?: boolean }) => {
      if (!listPrefsReady) return;
      const silent = opts?.silent === true;
      const gen = ++listLoadGenRef.current;
      if (!silent) {
        setListLoading(true);
        setListError("");
      } else {
        setListPolling(true);
      }
      try {
        const useDateFilter = (closedMode || assignedTo != null) && periodFilterActive;
        const data = await fetchOpenTrackerTickets({
          page: listPage,
          per_page: perPage,
          closed: closedMode,
          subscriber_q: subscriberQ || undefined,
          date_from: useDateFilter && dateFrom ? dateFrom : undefined,
          date_to: useDateFilter && dateTo ? dateTo : undefined,
          assigned_to: assignedTo,
        });
        if (gen !== listLoadGenRef.current) return;
        const applyRows = (items: TrackerTicketListItem[]) => {
          if (silent) {
            const prevIds = listRowIdsRef.current;
            const newIds = items.filter((r) => !prevIds.has(r.id)).map((r) => r.id);
            listRowIdsRef.current = new Set(items.map((r) => r.id));
            startTransition(() => {
              setListRows((prev) => mergeTrackerListPage(prev, items));
              if (newIds.length > 0) {
                setEnteringRowIds(new Set(newIds));
                window.setTimeout(() => setEnteringRowIds(new Set()), 320);
              }
            });
          } else {
            listRowIdsRef.current = new Set(items.map((r) => r.id));
            setEnteringRowIds(new Set());
            setListRows(items);
          }
        };
        applyRows(data.items);
        setListTotal(data.total);
        setListStats(data.stats);
        const totalPages = Math.max(1, Math.ceil(data.total / perPage));
        if (listPage > totalPages) {
          setListPage(totalPages);
        }
        try {
          const dig = await fetchTrackerListDigest({
            page: listPage,
            per_page: perPage,
            closed: closedMode,
            subscriber_q: subscriberQ || undefined,
            date_from: useDateFilter && dateFrom ? dateFrom : undefined,
            date_to: useDateFilter && dateTo ? dateTo : undefined,
            assigned_to: assignedTo,
          });
          if (gen === listLoadGenRef.current) {
            listDigestRef.current = dig.digest;
          }
        } catch {
          /* digest для следующего поллинга необязателен */
        }
      } catch (e) {
        if (gen !== listLoadGenRef.current) return;
        if (!silent) {
          setListError(e instanceof Error ? e.message : "Ошибка загрузки");
        }
      } finally {
        if (gen !== listLoadGenRef.current) return;
        if (!silent) setListLoading(false);
        else setListPolling(false);
      }
    },
    [listPrefsReady, listPage, perPage, closedMode, subscriberQ, dateFrom, dateTo, assignedTo, periodFilterActive],
  );

  useEffect(() => {
    listDigestRef.current = null;
  }, [listPage, perPage, closedMode, subscriberQ, dateFrom, dateTo, assignedTo]);

  useEffect(() => {
    if (!listMode || !listPrefsReady) return;
    void loadTicketsList();
  }, [listMode, listPrefsReady, loadTicketsList]);

  const pollTicketsList = useCallback(async () => {
    if (!listPrefsReady || document.visibilityState === "hidden") return;
    setListPolling(true);
    try {
      const useDateFilter = (closedMode || assignedTo != null) && periodFilterActive;
      const dig = await fetchTrackerListDigest({
        page: listPage,
        per_page: perPage,
        closed: closedMode,
        subscriber_q: subscriberQ || undefined,
        date_from: useDateFilter && dateFrom ? dateFrom : undefined,
        date_to: useDateFilter && dateTo ? dateTo : undefined,
        assigned_to: assignedTo,
        digest: listDigestRef.current ?? undefined,
      });
      listDigestRef.current = dig.digest;
      if (dig.changed) {
        await loadTicketsList({ silent: true });
      } else {
        setListTotal((prev) => (prev !== dig.total ? dig.total : prev));
      }
    } catch {
      await loadTicketsList({ silent: true });
    } finally {
      setListPolling(false);
    }
  }, [
    listPrefsReady,
    listPage,
    perPage,
    closedMode,
    subscriberQ,
    dateFrom,
    dateTo,
    assignedTo,
    periodFilterActive,
    loadTicketsList,
  ]);

  useEffect(() => {
    if (!listMode || !listPrefsReady) return;

    const schedule = () => {
      const jitter = Math.floor(Math.random() * TICKETS_LIST_POLL_JITTER_MS);
      pollTimerRef.current = window.setTimeout(() => {
        void pollTicketsList().finally(schedule);
      }, TICKETS_LIST_POLL_MS + jitter);
    };

    const onVisible = () => {
      if (document.visibilityState === "visible") void pollTicketsList();
    };

    schedule();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      if (pollTimerRef.current != null) window.clearTimeout(pollTimerRef.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [listMode, listPrefsReady, pollTicketsList]);

  function handlePerPageChange(next: TicketsListPerPage) {
    setPerPage(next);
    setListPage(1);
    const uid = viewerIdRef.current;
    if (uid != null) saveTicketsPerPage(uid, next);
  }

  function setClosedMode(nextClosed: boolean) {
    const next = new URLSearchParams(params);
    if (nextClosed) next.set("closed", "true");
    else {
      next.delete("closed");
      next.delete("date_from");
      next.delete("date_to");
    }
    setParams(next, { replace: true });
    setListPage(1);
  }

  function setDateFilter(key: "date_from" | "date_to", value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
    setListPage(1);
  }

  function openChatFromApi(row: TrackerTicketListItem) {
    navigate(`/tickets/${row.id}`);
  }

  function back() {
    navigate("/tickets", { replace: true, state: {} });
    setListMode(true);
  }

  function send() {
    const t = input.trim();
    if (!t) return;
    const time = `${new Date().getHours()}:${String(new Date().getMinutes()).padStart(2, "0")}`;
    setMsgs((m) => [
      ...m,
      {
        id: crypto.randomUUID(),
        side: mode === "n" ? "note" : "ag",
        text: t,
        time,
      },
    ]);
    setInput("");
  }

  function runDiag() {
    if (diagRun) return;
    setDiagRun(true);
    const steps = ["Проверка логина / ID…", "Проверка тарифа…", "Проверка баланса…", "Проверка станции…"];
    let i = 0;
    setDiagStep(steps[0]);
    const iv = window.setInterval(() => {
      i += 1;
      if (i < steps.length) setDiagStep(steps[i]);
      else {
        window.clearInterval(iv);
        setDiagRun(false);
        setDiagStep("");
      }
    }, 700);
  }

  if (listMode) {
    const totalPages = Math.max(1, Math.ceil(listTotal / perPage));
    const tableClass = closedMode ? "ch-table-wrap ch-table-wrap--closed" : "ch-table-wrap";

    function renderTicketCell(row: TrackerTicketListItem) {
      return (
        <div className="ch-row-main">
          <div className="ch-row-head">
            {row.source === "call_center" ? (
              <span className="ch-call-ico" title="Зарегистрирован после звонка на горячую линию">
                <CallCenterPhoneIcon />
              </span>
            ) : null}
            {row.object_type === "user" && (row.subscriber_is_juridical ?? 0) === 2 ? (
              <span className="ch-jur-mark" title="Юридическое лицо">
                ЮЛ
              </span>
            ) : null}
            <span className="ch-row-id">#{row.id}</span>
            {!closedMode && ticketListNeedsAttention(row) ? (
              <span className="ch-unread-dot" title="Нужен ответ" />
            ) : null}
            <span className="ch-row-title" title={row.title}>
              {row.title}
            </span>
          </div>
          {row.object_type === "user" && row.subscriber_profile_user_id != null && (row.subscriber_name || "").trim() ? (
            <Link
              className="ch-row-userlink"
              to={`/users/${row.subscriber_profile_user_id}`}
              title={row.subscriber_name ?? undefined}
              onClick={(e) => e.stopPropagation()}
            >
              {row.subscriber_name}
            </Link>
          ) : null}
          {row.category_label ? (
            <span className="ch-row-cat" title={row.category_label}>
              {row.category_label}
            </span>
          ) : null}
        </div>
      );
    }

    function renderRow(row: TrackerTicketListItem) {
      const statusCol = ticketListStatusColumn(row);
      const assigneePill = ticketListAssigneePill(row);
      const needsAttention = !closedMode && ticketListNeedsAttention(row);
      const workEnd = closedMode ? row.date_of_close || row.updated_at : null;
      const workDuration = closedMode
        ? formatWorkDurationBetween(row.date_of_create, workEnd, nowPulse)
        : formatWorkDurationSince(row.date_of_create, nowPulse);

      return (
        <div
          key={row.id}
          className={`ch-row${needsAttention ? " ch-row--unread" : ""}${closedMode ? " ch-row--closed" : ""}${enteringRowIds.has(row.id) ? " ch-row--enter" : ""}`}
          role="button"
          tabIndex={0}
          onClick={() => openChatFromApi(row)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openChatFromApi(row);
            }
          }}
        >
          {renderTicketCell(row)}
          {!closedMode ? (
            <span
              className={`ch-priority ch-priority--${row.priority ?? "middle"}`}
              title={row.priority_label ?? "Средний"}
            >
              {row.priority_label ?? "Средний"}
            </span>
          ) : null}
          <div className="ch-status-cell">
            {statusCol.kind === "comm" ? (
              <span className={`ch-comm ch-comm--${statusCol.state}`} title={statusCol.label}>
                {statusCol.label}
              </span>
            ) : (
              <span className={`ch-status ch-status--${statusCol.status}`} title={statusCol.label}>
                {statusCol.label}
              </span>
            )}
          </div>
          {!closedMode ? (
            <>
              <div className="ch-exec-cell">
                <span
                  className={`ch-assignee-pill ch-assignee-pill--${assigneePill.variant}`}
                  title={assigneePill.title ?? assigneePill.label}
                >
                  {assigneePill.label}
                </span>
              </div>
              <span
                className={`ch-line ch-line--${queueLineBadgeClass(row.queue_line ?? "cs")}`}
                title={row.support_line_label}
              >
                {queueLineShortLabel(row.queue_line ?? "cs", row.support_line)}
              </span>
              <span className="ch-muted ch-mono">{formatTicketUpdatedLocal(row.date_of_create)}</span>
              <span className="ch-muted ch-mono">{workDuration}</span>
              <span className="ch-muted ch-time ch-mono">
                {formatTicketUpdatedLocal(row.updated_at || row.date_of_create)}
              </span>
            </>
          ) : (
            <>
              <span className="ch-muted ch-mono">{formatTicketUpdatedLocal(row.date_of_create)}</span>
              <span className="ch-muted ch-mono">{workDuration}</span>
              <div className="ch-rating-cell" title={row.rating_comment ?? undefined}>
                <RatingStars value={row.rating} />
                {row.rating_comment ? (
                  <span className="ch-rating-comment">{row.rating_comment}</span>
                ) : null}
              </div>
              <span className="ch-muted ch-time ch-mono">
                {formatTicketUpdatedLocal(row.date_of_close || row.updated_at || row.date_of_create)}
              </span>
            </>
          )}
        </div>
      );
    }

    return (
      <div className="tp on">
        <div className="pg">
          <div className="ch-list-head">
            <div>
              <div className="ch-list-title">
              {closedMode ? "Закрытые тикеты" : "Тикеты"}
              {listPolling ? (
                <span className="ch-list-poll" title="Обновление списка…" aria-hidden />
              ) : null}
            </div>
            </div>
            <div className="ch-list-toolbar">
              <label className="ch-per-label">
                На странице
                <select
                  className="ch-per-select"
                  value={perPage}
                  onChange={(e) => {
                    handlePerPageChange(Number(e.target.value) as TicketsListPerPage);
                  }}
                >
                  {TICKETS_LIST_PER_PAGE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className={`ch-mode-btn${closedMode ? " ch-mode-btn--active" : ""}`}
                onClick={() => setClosedMode(!closedMode)}
              >
                {closedMode ? "Открытые" : "Закрытые"}
              </button>
            </div>
          </div>

          {closedMode ? (
            <div className="ch-closed-stats" aria-label="Статистика закрытых тикетов">
              <div className="ch-stat-pill">
                <span className="ch-stat-pill__label">Всего закрытых</span>
                <span className="ch-stat-pill__val">{listTotal}</span>
              </div>
              <div className={`ch-stat-pill ch-stat-pill--rated ${ratingToneClass(listStats?.avg_rating ?? null)}`.trim()}>
                <span className="ch-stat-pill__label">Средний рейтинг</span>
                <span className="ch-stat-pill__val">{formatRatingAvg(listStats?.avg_rating ?? null)}</span>
              </div>
              <div className={`ch-stat-pill ch-stat-pill--rated ${ratingToneClass(listStats?.avg_rating_mine ?? null)}`.trim()}>
                <span className="ch-stat-pill__label">Мой рейтинг</span>
                <span className="ch-stat-pill__val">{formatRatingAvg(listStats?.avg_rating_mine ?? null)}</span>
              </div>
            </div>
          ) : null}

          <div className="ch-filters">
            <label className="ch-filter-field ch-filter-field--grow">
              <span className="ch-filter-label">Абонент</span>
              <input
                type="search"
                className="ch-filter-input"
                placeholder="ФИО, id или логин"
                value={subscriberInput}
                onChange={(e) => setSubscriberInput(e.target.value)}
              />
            </label>
            {closedMode ? (
              <div className="ch-date-range">
                <span className="ch-filter-label ch-date-range-label">Период закрытия</span>
                <div className="ch-date-range-row">
                  <div className="ch-date-field">
                    <span className="ch-date-field-cap">С</span>
                    <DatePickerField
                      value={dateFrom}
                      onChange={(v) => setDateFilter("date_from", v)}
                      placeholder="дд.мм.гггг"
                    />
                  </div>
                  <span className="ch-date-range-sep" aria-hidden>
                    —
                  </span>
                  <div className="ch-date-field">
                    <span className="ch-date-field-cap">По</span>
                    <DatePickerField
                      value={dateTo}
                      minDate={dateFrom || undefined}
                      onChange={(v) => setDateFilter("date_to", v)}
                      placeholder="дд.мм.гггг"
                    />
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {listError ? <div className="ch-list-err">{listError}</div> : null}
          {listLoading ? <div className="ch-list-loading">Загрузка…</div> : null}

          <div className={tableClass}>
            <div className={`ch-list-meta-row ch-list-thead${closedMode ? " ch-list-thead--closed" : ""}`}>
              <span>Тикет</span>
              {closedMode ? (
                <>
                  <span>Статус</span>
                  <span>Открыт</span>
                  <span>В работе</span>
                  <span>Оценка</span>
                  <span>Закрыт</span>
                </>
              ) : (
                <>
                  <span>Приоритет</span>
                  <span>Статус</span>
                  <span>Исполнитель</span>
                  <span>Линия</span>
                  <span>Открыт</span>
                  <span>В работе</span>
                  <span>Обновлён</span>
                </>
              )}
            </div>

            <div className="ch-list-body">{listRows.map(renderRow)}</div>
          </div>

          {!listLoading && listRows.length === 0 && !listError ? (
            <div className="ch-list-empty">
              {closedMode ? "Нет закрытых тикетов" : "Нет открытых тикетов"}
            </div>
          ) : null}

          <div className="ch-pager">
            <button
              type="button"
              className="ch-page-btn"
              disabled={listPage <= 1 || listLoading}
              onClick={() => setListPage((p) => Math.max(1, p - 1))}
            >
              Назад
            </button>
            <span className="ch-page-info">
              Стр. {listPage} / {totalPages} · всего {listTotal}
            </span>
            <button
              type="button"
              className="ch-page-btn"
              disabled={listPage >= totalPages || listLoading}
              onClick={() => setListPage((p) => p + 1)}
            >
              Вперёд
            </button>
          </div>
        </div>
      </div>
    );
  }

  const stLabel =
    ticket.status === "new" ? "Новая" : ticket.status === "wait" ? "Ожидание" : "В работе";
  const stClass = ticket.status === "new" ? "tn" : ticket.status === "wait" ? "tw" : "tk";

  return (
    <div className="tp on" id="tp-tickets" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden", position: "relative" }}>
        <div className="tbar">
          <button type="button" className="tbk" onClick={back}>
            ← Назад
          </button>
          <div style={{ width: 1, height: 16, background: "var(--ln)" }} />
          <div className="ttl">{ticket.topic}</div>
          <div className="tid">#{ticket.id}</div>
          <span className={`tag ${stClass}`}>{stLabel}</span>
          <div className="tacts">
            <button type="button" className={`diag-btn${diagRun ? " running" : ""}`} onClick={runDiag}>
              <svg width="13" height="13" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M2 15h3l2-5 3 8 2-10 2 4h4" />
                <circle cx="17" cy="12" r="1.5" fill="currentColor" stroke="none" />
              </svg>
              {diagRun ? "Проверяю…" : "Проверка"}
            </button>
            <button type="button" className="tb3">
              Инженерам
            </button>
            <button type="button" className="tb3 kbo" onClick={() => setKbOpen(true)}>
              База знаний
            </button>
            <button type="button" className="tb3 cls">
              Завершить
            </button>
            <button type="button" className="tb3" onClick={() => setSideOpen((v) => !v)}>
              ≡
            </button>
          </div>
        </div>
        <div className="tbody">
          <div className={`diag-overlay ${diagRun ? "vis" : ""}`}>
            <div className="diag-spinner" />
            <div className={`diag-step${diagRun ? " vis" : ""}`}>{diagStep}</div>
          </div>
          <div className="czone">
            <div className="cscrl">
              <div className="dsep">
                <span>19 марта</span>
              </div>
              {msgs.map((m) => (
                <div key={m.id} className={`msg ${m.side === "cl" ? "cl" : "me"}`}>
                  <div className={`mav ${m.side === "cl" ? "cl" : m.side === "note" ? "cl" : "ag"}`}>
                    {m.side === "cl" ? (ticket.name?.trim()?.[0] ?? "?") : m.side === "note" ? "З" : "КЦ"}
                  </div>
                  <div className="mc2">
                    {m.side === "note" ? (
                      <div className="bbl nt">
                        <div className="ntb">Заметка</div>
                        {m.text}
                      </div>
                    ) : (
                      <div className={`bbl ${m.side === "cl" ? "cl" : "ag"}`}>{m.text}</div>
                    )}
                    <div className="mtm">{m.time}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="comp">
              <div className="ctbs">
                <button type="button" className={`ct2${mode === "r" ? " on" : ""}`} onClick={() => setMode("r")}>
                  Ответ клиенту
                </button>
                <button type="button" className={`ct2 nt2${mode === "n" ? " on" : ""}`} onClick={() => setMode("n")}>
                  Внутренняя заметка
                </button>
              </div>
              {mode === "r" ? (
                <div className="cq" id="cqW">
                  <span className="cql">Быстрые ответы:</span>
                  {["Здравствуйте! Чем могу помочь?", "Уточню, подождите.", "Перезагрузите роутер: выключите на 30 сек."].map(
                    (x) => (
                      <button key={x} type="button" className="chip" onClick={() => setInput(x)}>
                        {x.slice(0, 22)}…
                      </button>
                    ),
                  )}
                </div>
              ) : null}
              <div className="crow">
                <textarea
                  className={`cf${mode === "n" ? " nm" : ""}`}
                  rows={2}
                  placeholder={mode === "n" ? "Заметка…" : "Ответ клиенту…"}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.ctrlKey && e.key === "Enter") send();
                  }}
                />
                <button type="button" className={`csb${mode === "n" ? " ns" : ""}`} onClick={send}>
                  →
                </button>
              </div>
              <div className="ch">Ctrl+Enter — отправить</div>
            </div>
          </div>
          <aside className={`ip${sideOpen ? "" : " closed"}`} id="cdIP">
            <div className="ips">
              <div className="ipb">
                <div className="ipl">Абонент</div>
                <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 2 }}>{ticket.name}</div>
                <div style={{ fontSize: 10, color: "var(--i3)", marginBottom: 4 }}>
                  ID: {sub.id} · {sub.c}
                </div>
                <div className={`ltv ${sub.ltv}`}>{sub.ltvT}</div>
              </div>
              <div className="ipb">
                <div className="ipl">Тариф и баланс</div>
                <div className="kv">
                  <span className="kvk">Тариф</span>
                  <span className="kvv">{sub.t}</span>
                </div>
                <div className="kv">
                  <span className="kvk">Баланс</span>
                  <span className="kvv ok big">{sub.bal}</span>
                </div>
              </div>
              <div className="sh2">
                <div className="shh">Подсказка</div>
                <div className="shs">
                  <div className="shn">1</div>
                  <span>Проверить статус станции</span>
                </div>
                <div className="shs">
                  <div className="shn">2</div>
                  <span>Перезагрузить роутер</span>
                </div>
              </div>
            </div>
          </aside>
          <div className={`kbp${kbOpen ? " open" : ""}`} id="kbP">
            <div className="kbph">
              <input
                type="search"
                placeholder="Поиск в базе…"
                value={kbFilter}
                onChange={(e) => setKbFilter(e.target.value)}
              />
              <button type="button" className="kbpx" onClick={() => setKbOpen(false)}>
                ×
              </button>
            </div>
            <div className="kbpb">
              {filteredKb.map((k) => (
                <div key={k.t} className="kbr open">
                  <div className="kbrt">{k.t}</div>
                  <div className="kbrd" dangerouslySetInnerHTML={{ __html: k.b }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
