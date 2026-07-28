import { useCallback, useEffect, useState } from "react";
import { fetchUserSessions, type SessionHistoryItem } from "@/api/userProfile";

const PER_PAGE = 10;

type Props = {
  userId: number;
};

export default function SessionsHistoryPanel({ userId }: Props) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<SessionHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));

  const loadPage = useCallback(
    (p: number) => {
      setPage(p);
      setLoading(true);
      setErr(null);
      fetchUserSessions(userId, p, PER_PAGE)
        .then((r) => {
          setItems(r.items);
          setTotal(r.total);
        })
        .catch((e: unknown) => {
          setItems([]);
          setTotal(0);
          setErr(e instanceof Error ? e.message : "Не удалось загрузить сессии");
        })
        .finally(() => setLoading(false));
    },
    [userId],
  );

  useEffect(() => {
    loadPage(1);
  }, [loadPage]);

  if (loading && items.length === 0) {
    return <p className="up-muted">Загрузка…</p>;
  }

  if (err) {
    return <p className="up-muted up-error">{err}</p>;
  }

  if (items.length === 0) {
    return <p className="up-muted">Сессий не найдено</p>;
  }

  return (
    <div className="up-sessions-hist">
      <p className="up-history-tz-note">Дата и время указаны по московскому времени (МСК).</p>
      <table className="dt up-sessions-hist-table">
        <thead>
          <tr>
            <th>Начало (МСК)</th>
            <th>Завершение</th>
            <th>Трафик</th>
            <th>IP / Станция</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={`${row.started_at}-${row.ip_address}-${i}`}>
              <td className="up-sessions-hist-date">{row.started_at_label}</td>
              <td>
                {row.is_open ? (
                  <span className="up-sessions-hist-open">Открытая сессия</span>
                ) : (
                  <span className="up-sessions-hist-date">{row.stopped_at_label}</span>
                )}
                <div className="up-sessions-hist-duration" title="Длительность сессии">
                  {row.duration_label}
                </div>
              </td>
              <td className="up-sessions-hist-traffic">
                <div className="up-sessions-hist-traffic-total" title="Всего">
                  {row.traffic_total_label}
                </div>
                <div className="up-sessions-hist-traffic-io">
                  <span title="Входящий трафик">↓ {row.traffic_in_label}</span>
                  <span title="Исходящий трафик">↑ {row.traffic_out_label}</span>
                </div>
              </td>
              <td className="up-sessions-hist-endpoint">
                <div className="up-sessions-hist-ip">{row.ip_address}</div>
                <div className="up-sessions-hist-station">{row.station_name ?? "—"}</div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {total > PER_PAGE ? (
        <div className="ch-pager up-sessions-hist-pager">
          <button
            type="button"
            className="ch-page-btn"
            disabled={page <= 1 || loading}
            onClick={() => loadPage(Math.max(1, page - 1))}
          >
            Назад
          </button>
          <span className="ch-page-info">
            Стр. {page} / {totalPages} · всего {total}
          </span>
          <button
            type="button"
            className="ch-page-btn"
            disabled={page >= totalPages || loading}
            onClick={() => loadPage(page + 1)}
          >
            Вперёд
          </button>
        </div>
      ) : null}
    </div>
  );
}
