import type { ProfileOpenSession } from "@/api/userProfile";

type Props = {
  sessions: ProfileOpenSession[];
};

export default function OpenSessionsCard({ sessions }: Props) {
  const count = sessions.length;

  return (
    <div className="card up-card up-sessions">
      <div className="up-card-head up-sessions-head">
        <div className="ct">Активные сессии</div>
        <span
          className={`up-sessions-count${count === 0 ? " up-sessions-count--zero" : ""}`}
          aria-label={`Открытых сессий: ${count}`}
        >
          {count}
        </span>
      </div>
      {sessions.length === 0 ? (
        <p className="up-muted up-sessions-empty">Нет активных сессий</p>
      ) : (
        <div className="up-sessions-list">
          {sessions.map((s, i) => (
            <div
              key={`${s.ip_address}-${s.started_at}-${s.protocol}-${i}`}
              className="up-sess-item"
            >
              <div className="up-sess-top">
                <div className="up-sess-title">
                  <span className="up-sess-dot" aria-hidden />
                  <span>{sessions.length > 1 ? `Сессия ${i + 1}` : "Активная сессия"}</span>
                </div>
                <span
                  className={`up-sess-type${s.protocol === "PPPoE" ? " up-sess-type--pppoe" : " up-sess-type--hotspot"}`}
                >
                  {s.protocol === "PPPoE" ? "PPPoE" : "Hotspot"}
                </span>
              </div>
              <div className="up-sess-meta">
                <span>
                  С: <strong>{s.started_at_label}</strong>
                </span>
                <span>
                  IP: <strong>{s.ip_address}</strong>
                </span>
                <span>
                  В работе: <strong>{s.duration_label}</strong>
                </span>
                <span>
                  Станция: <strong>{s.station_name ?? "—"}</strong>
                </span>
                <span className="up-sess-traffic">
                  <span title="Входящий трафик">
                    ↓ <strong>{s.traffic_in_label}</strong>
                  </span>
                  {" / "}
                  <span title="Исходящий трафик">
                    ↑ <strong>{s.traffic_out_label}</strong>
                  </span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
