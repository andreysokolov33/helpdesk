import { useNavigate } from "react-router-dom";
import UniversalSearch from "@/components/UniversalSearch";
import { MOCK_RATINGS, MOCK_TICKETS_OPEN, MOCK_TICKETS_URGENT } from "@/data/mockCc";

export default function HomeTab() {
  const navigate = useNavigate();

  return (
    <div className="tp on">
      <div className="pg">
        <div style={{ textAlign: "center", padding: "8px 0 4px" }}>
          <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 14 }}>
            Найдите <span style={{ color: "var(--red)" }}>абонента</span> или ответ в{" "}
            <span style={{ color: "var(--red)" }}>базе знаний</span>
          </div>
          <UniversalSearch />
        </div>

        <p style={{ fontSize: 12, color: "var(--i2)", textAlign: "center", marginTop: 8 }}>
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
                onClick={() => navigate(`/tickets/${t.id}`)}
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
                onClick={() => navigate(`/tickets/${t.id}`)}
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
                    <button type="button" className="lb" onClick={() => navigate("/tickets")}>
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
