import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { MOCK_KB, MOCK_SUBSCRIBERS, MOCK_TICKETS_OPEN, MOCK_TICKETS_URGENT } from "@/data/mockCc";

const ALL = [...MOCK_TICKETS_URGENT, ...MOCK_TICKETS_OPEN];

type ChatMsg = { id: string; side: "cl" | "ag" | "note"; text: string; time: string };

const initialMsgs: ChatMsg[] = [
  { id: "1", side: "cl", text: "Здравствуйте! Где посмотреть детализацию?", time: "14:03" },
  { id: "2", side: "ag", text: "Здравствуйте! Сейчас помогу", time: "14:05" },
];

export default function ChatsTab() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const idParam = Number(params.get("id")) || 301;
  const ticket = useMemo(() => ALL.find((t) => t.id === idParam) ?? ALL[0], [idParam]);
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

  function openChat(tid: number) {
    navigate(`/chats?id=${tid}`);
    setListMode(false);
  }

  function back() {
    navigate("/chats");
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
    return (
      <div className="tp on">
        <div className="pg">
          <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 4 }}>Диалоги</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {ALL.map((t) => (
              <button type="button" key={t.id} className="tl" onClick={() => openChat(t.id)}>
                <div className="tln">#{t.id}</div>
                <div
                  className="tld"
                  style={{
                    background:
                      t.dot === "red" ? "var(--red)" : t.dot === "wn" ? "var(--wn)" : "var(--i2)",
                  }}
                />
                <div className="tlnm">{t.name}</div>
                <div className="tltp">{t.topic}</div>
                <span className={`tag ${t.status === "new" ? "tn" : t.status === "wait" ? "tw" : "tk"}`}>
                  {t.status === "new" ? "Новая" : t.status === "wait" ? "Ожидание" : "В работе"}
                </span>
                <div className="tlt">{t.time}</div>
              </button>
            ))}
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
                    {m.side === "cl" ? ticket.name[0] : m.side === "note" ? "З" : "КЦ"}
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
