import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  MOCK_KB,
  MOCK_RATINGS,
  MOCK_SUBSCRIBERS,
  MOCK_TICKETS_OPEN,
  MOCK_TICKETS_URGENT,
  type KbArticle,
} from "@/data/mockCc";

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, "").slice(0, 80);
}

export default function HomeTab() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [openDrop, setOpenDrop] = useState(false);
  const [kbOpen, setKbOpen] = useState(false);
  const [kbTitle, setKbTitle] = useState("");
  const [kbBody, setKbBody] = useState("");

  const subs = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (s.length < 2) return [];
    return MOCK_SUBSCRIBERS.filter(
      (x) =>
        x.n.toLowerCase().includes(s) ||
        String(x.id).includes(s) ||
        x.c.toLowerCase().includes(s) ||
        x.a.toLowerCase().includes(s),
    );
  }, [q]);

  const kb = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (s.length < 2) return [];
    return MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
  }, [q]);

  function onSearchInput(v: string) {
    setQ(v);
    setOpenDrop(v.trim().length >= 2 && (subs.length > 0 || kb.length > 0));
    setKbOpen(false);
  }

  function showKbCard(article: KbArticle) {
    setKbTitle(article.t);
    setKbBody(article.b);
    setKbOpen(true);
    setOpenDrop(false);
    setQ("");
  }

  function onSearchEnter() {
    const s = q.trim().toLowerCase();
    if (!s) return;
    setOpenDrop(false);
    const kh = MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
    if (kh.length) {
      showKbCard(kh[0]);
      return;
    }
    const sh = MOCK_SUBSCRIBERS.filter(
      (x) => x.n.toLowerCase().includes(s) || String(x.id).includes(s),
    );
    if (sh.length) setQ(sh[0].n);
  }

  return (
    <div className="tp on">
      <div className="pg">
        <div style={{ textAlign: "center", padding: "8px 0 4px" }}>
          <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 10 }}>
            Найдите <span style={{ color: "var(--red)" }}>абонента</span> или ответ в{" "}
            <span style={{ color: "var(--red)" }}>базе знаний</span>
          </div>
          <div className="sw" style={{ maxWidth: 620, margin: "0 auto" }}>
            <input
              className="si"
              value={q}
              onChange={(e) => onSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSearchEnter()}
              placeholder="ФИО, ID, адрес · или запрос: «платёж не пришёл», «перезагрузка роутера»…"
              autoComplete="off"
            />
            <svg className="sic" width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden>
              <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M14 14l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <div className={`sd ${openDrop ? "vis" : ""}`}>
              {subs.length > 0 ? (
                <>
                  <div className="ssc">Абоненты</div>
                  {subs.map((s) => (
                    <button
                      type="button"
                      key={s.id}
                      className="si2"
                      onClick={() => {
                        setQ(s.n);
                        setOpenDrop(false);
                      }}
                    >
                      <div className="sav">{s.n[0]}</div>
                      <div style={{ flex: 1, textAlign: "left" }}>
                        <div className="sn">{s.n}</div>
                        <div className="sm">
                          ID {s.id} · {s.a} · {s.c}
                        </div>
                      </div>
                    </button>
                  ))}
                </>
              ) : null}
              {kb.length > 0 ? (
                <>
                  <div className="ssc">База знаний</div>
                  {kb.slice(0, 5).map((k) => (
                    <button type="button" key={k.t} className="si2" onClick={() => showKbCard(k)}>
                      <div className="sav kb">БЗ</div>
                      <div style={{ flex: 1, textAlign: "left" }}>
                        <div className="sn">{k.t}</div>
                        <div className="sm">{stripHtml(k.b)}…</div>
                      </div>
                    </button>
                  ))}
                </>
              ) : null}
            </div>
          </div>
        </div>

        <div className={`kbc ${kbOpen ? "vis" : ""}`}>
          <button type="button" className="kbc-x" aria-label="Закрыть" onClick={() => setKbOpen(false)}>
            ×
          </button>
          <div className="kbc-t">
            {kbTitle} <span className="kbc-tag">Инструкция</span>
          </div>
          <div className="kbc-b" dangerouslySetInnerHTML={{ __html: kbBody }} />
        </div>

        <p style={{ fontSize: 12, color: "var(--i2)", textAlign: "center" }}>
          Сегодня <strong style={{ color: "var(--ink)" }}>10 заявок</strong> —{" "}
          <span style={{ color: "var(--red)", fontWeight: 600 }}>2 ждут ответа</span>
        </p>

        <div>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: "var(--i3)",
              textTransform: "uppercase",
              letterSpacing: "0.6px",
              marginBottom: 7,
            }}
          >
            Ждут ответа
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {MOCK_TICKETS_URGENT.map((t) => (
              <button
                type="button"
                key={t.id}
                className="ug"
                onClick={() => navigate(`/chats?id=${t.id}`)}
              >
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: "var(--red)",
                    marginBottom: 3,
                    display: "flex",
                    alignItems: "center",
                    gap: 3,
                  }}
                >
                  <span className="pulse" /> {t.time}
                  {t.urgentLabel ? (
                    <span className="tag thi" style={{ marginLeft: 3 }}>
                      {t.urgentLabel}
                    </span>
                  ) : null}
                </div>
                <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 2 }}>{t.name}</div>
                <div style={{ fontSize: 10, color: "var(--i2)" }}>{t.topic}</div>
                <div
                  style={{
                    display: "inline-flex",
                    marginTop: 7,
                    fontSize: 10,
                    fontWeight: 700,
                    color: "var(--red)",
                    background: "var(--rbg)",
                    borderRadius: 4,
                    padding: "2px 7px",
                  }}
                >
                  Ответить →
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: "var(--i3)",
              textTransform: "uppercase",
              letterSpacing: "0.6px",
              marginBottom: 7,
            }}
          >
            Открытые заявки
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {MOCK_TICKETS_OPEN.map((t) => (
              <button
                type="button"
                key={t.id}
                className="tl"
                onClick={() => navigate(`/chats?id=${t.id}`)}
              >
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
                <span
                  className={`tag ${t.status === "new" ? "tn" : t.status === "wait" ? "tw" : "tk"}`}
                >
                  {t.status === "new" ? "Новая" : t.status === "wait" ? "Ожидание" : "В работе"}
                </span>
                <div className="tlt">{t.time}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="ct">Низкие оценки</div>
          <div className="cs2">Рекомендуется связаться повторно</div>
          <table className="dt">
            <thead>
              <tr>
                <th>Клиент</th>
                <th>Причина</th>
                <th>Оценка</th>
                <th>Дата</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {MOCK_RATINGS.map((r) => (
                <tr key={r.name}>
                  <td>
                    <strong>{r.name}</strong>
                  </td>
                  <td style={{ color: "var(--i2)" }}>{r.reason}</td>
                  <td style={{ color: r.score === "1" ? "var(--red)" : "var(--wn)", fontWeight: 700 }}>
                    {r.score}
                  </td>
                  <td style={{ color: "var(--i3)" }}>{r.date}</td>
                  <td>
                    <button type="button" className="lb" onClick={() => navigate(`/chats`)}>
                      Написать
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
