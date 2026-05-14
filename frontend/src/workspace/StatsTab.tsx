import { MOCK_CATEGORY_BARS, MOCK_STATS_CARDS } from "@/data/mockCc";

export default function StatsTab() {
  return (
    <div className="tp on">
      <div className="pg">
        <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 4 }}>Статистика</div>
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            flexWrap: "wrap",
            background: "var(--p)",
            border: "1.5px solid var(--ln)",
            borderRadius: "var(--r)",
            padding: "10px 14px",
          }}
        >
          <span style={{ fontSize: 9, fontWeight: 700, color: "var(--i3)", textTransform: "uppercase" }}>
            Период
          </span>
          <select className="msl" style={{ height: 28, fontSize: 11 }} defaultValue="week">
            <option value="today">Сегодня</option>
            <option value="week">Неделя</option>
            <option value="month">Месяц</option>
          </select>
        </div>
        <div className="g6">
          {MOCK_STATS_CARDS.map((c) => (
            <div key={c.label} className="mc">
              <div className="ml">
                {c.label}
                {c.tip ? (
                  <span className="mh" data-tip={c.tip}>
                    ?
                  </span>
                ) : null}
              </div>
              <div className={`mv ${c.mvClass}`}>
                {c.value} <span className={`dl ${c.deltaClass === "up" ? "up" : "dn"}`}>{c.delta}</span>
              </div>
              <div className="md">{c.sub}</div>
            </div>
          ))}
        </div>
        <div className="card">
          <div className="ct">По категориям</div>
          {MOCK_CATEGORY_BARS.map((b) => (
            <div key={b.label} className="br">
              <div className="blr">
                <span className="bt2">{b.label}</span>
                <span className="bp">{b.pct}%</span>
              </div>
              <div className="btr">
                <div className={`bf ${b.bar}`} style={{ width: `${b.pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
