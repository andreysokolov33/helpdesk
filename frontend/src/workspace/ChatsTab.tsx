import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { fetchOpenTrackerTickets, trackerApiRowToTicketRow, type TrackerTicketListItem } from "@/api/tracker";
import { formatTicketUpdatedLocal, formatWorkDurationSince } from "@/utils/ticketFormat";
import { MOCK_KB, MOCK_SUBSCRIBERS, MOCK_TICKETS_OPEN, MOCK_TICKETS_URGENT, type TicketRow } from "@/data/mockCc";

type ChatMsg = { id: string; side: "cl" | "ag" | "note"; text: string; time: string };

const initialMsgs: ChatMsg[] = [
  { id: "1", side: "cl", text: "Здравствуйте! Где посмотреть детализацию?", time: "14:03" },
  { id: "2", side: "ag", text: "Здравствуйте! Сейчас помогу", time: "14:05" },
];

export default function ChatsTab() {
  const [params] = useSearchParams();
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
  const [listPage, setListPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState("");
  const [nowPulse, setNowPulse] = useState(() => Date.now());

  useEffect(() => {
    if (!listMode) return;
    const id = window.setInterval(() => setNowPulse(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, [listMode]);

  useEffect(() => {
    if (!listMode) return;
    let cancelled = false;
    (async () => {
      setListLoading(true);
      setListError("");
      try {
        const data = await fetchOpenTrackerTickets({ page: listPage, per_page: perPage, closed: false });
        if (cancelled) return;
        setListRows(data.items);
        setListTotal(data.total);
      } catch (e) {
        if (!cancelled) setListError(e instanceof Error ? e.message : "Ошибка загрузки");
      } finally {
        if (!cancelled) setListLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [listMode, listPage, perPage]);

  function openChatFromApi(row: TrackerTicketListItem) {
    const tr = trackerApiRowToTicketRow(row);
    navigate(`/chats?id=${row.id}`, { state: { ticketRow: tr } });
    setListMode(false);
  }

  function back() {
    navigate("/chats", { replace: true, state: {} });
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
    return (
      <div className="tp on">
        <div className="pg">
          <div className="ch-list-head">
            <div>
              <div className="ch-list-title">Тикеты</div>
            </div>
            <div className="ch-list-toolbar">
              <label className="ch-per-label">
                На странице
                <select
                  className="ch-per-select"
                  value={perPage}
                  onChange={(e) => {
                    setPerPage(Number(e.target.value));
                    setListPage(1);
                  }}
                >
                  {[10, 20, 50, 100].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {listError ? <div className="ch-list-err">{listError}</div> : null}
          {listLoading ? <div className="ch-list-loading">Загрузка…</div> : null}

          <div className="ch-table-wrap">
            <div className="ch-list-meta-row ch-list-thead">
              <span>Тикет</span>
              <span>Статус</span>
              <span>В работе</span>
              <span>Исполнитель</span>
              <span>Обновлён</span>
            </div>

            <div className="ch-list-body">
              {listRows.map((row) => (
                <div
                  key={row.id}
                  className="ch-row"
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
                  <div className="ch-row-main">
                    <div className="ch-row-head">
                      <span className="ch-row-id">#{row.id}</span>
                      <span
                        className={
                          row.object_type === "user" && (row.subscriber_is_juridical ?? 0) === 2
                            ? "ch-row-title ch-row-title--jur"
                            : "ch-row-title"
                        }
                        title={row.title}
                      >
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
                  <span className={`ch-status ch-status--${row.status}`}>{row.status_label}</span>
                  <span className="ch-muted ch-mono">{formatWorkDurationSince(row.date_of_create, nowPulse)}</span>
                  <div className="ch-exec-cell">
                    <span
                      className={`ch-line ch-line--${
                        row.support_line === 1 || row.support_line === 2 || row.support_line === 3
                          ? row.support_line
                          : "o"
                      }`}
                    >
                      {row.support_line_label}
                    </span>
                    {row.assignee_is_viewer ? <span className="ch-you-pill">Вы</span> : null}
                  </div>
                  <span className="ch-muted ch-time ch-mono">
                    {formatTicketUpdatedLocal(row.updated_at || row.date_of_create)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {!listLoading && listRows.length === 0 && !listError ? (
            <div className="ch-list-empty">Нет открытых тикетов</div>
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
    <div className="tp on" id="tp-chats" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
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
