import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchUserProfileTickets, type ProfileTicket } from "@/api/userProfile";

const PER_PAGE = 10;

function fmtDt(iso: string) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type Props = {
  userId: number;
};

export default function TicketsHistoryPanel({ userId }: Props) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ProfileTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));

  const loadPage = useCallback(
    (p: number) => {
      setPage(p);
      setLoading(true);
      setErr(null);
      fetchUserProfileTickets(userId, p, PER_PAGE)
        .then((r) => {
          setItems(r.items);
          setTotal(r.total);
        })
        .catch((e: unknown) => {
          setItems([]);
          setTotal(0);
          setErr(e instanceof Error ? e.message : "Не удалось загрузить обращения");
        })
        .finally(() => setLoading(false));
    },
    [userId],
  );

  useEffect(() => {
    loadPage(1);
  }, [loadPage]);

  if (loading && items.length === 0) {
    return <p className="up-muted">Загрузка обращений…</p>;
  }

  if (err) {
    return <p className="up-muted up-error">{err}</p>;
  }

  if (items.length === 0) {
    return (
      <div className="up-tickets-empty" role="status">
        <div className="up-tickets-empty__title">Обращений пока не было</div>
        <p className="up-tickets-empty__text">
          У этого абонента ещё не создавались обращения в техническую поддержку.
        </p>
      </div>
    );
  }

  return (
    <div className="up-appeals">
      <table className="dt up-appeals-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Тема</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr
              key={t.id}
              className="up-ticket-row"
              role="link"
              tabIndex={0}
              onClick={() => navigate(`/tickets/${t.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  navigate(`/tickets/${t.id}`);
                }
              }}
            >
              <td className="up-appeals-date">{fmtDt(t.date_of_create)}</td>
              <td className="up-appeals-topic">
                <strong>#{t.id} {t.title}</strong>
              </td>
              <td>
                <span className={`ch-status ch-status--${t.status}`}>{t.status_label}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {total > PER_PAGE ? (
        <div className="ch-pager up-appeals-pager">
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
