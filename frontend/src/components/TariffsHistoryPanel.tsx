import { useCallback, useEffect, useState } from "react";
import {
  fetchUserTariffHistory,
  type TariffHistoryItem,
} from "@/api/userProfile";

const PER_PAGE = 10;

function typeBadgeClass(row: TariffHistoryItem) {
  if (row.row_kind === "dop") return "up-tariff-badge up-tariff-badge--dop";
  return row.type_label === "Лимитный"
    ? "up-tariff-badge up-tariff-badge--limited"
    : "up-tariff-badge up-tariff-badge--unlim";
}

type Props = {
  userId: number;
};

export default function TariffsHistoryPanel({ userId }: Props) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<TariffHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));

  const loadPage = useCallback(
    (p: number) => {
      setPage(p);
      setLoading(true);
      setErr(null);
      fetchUserTariffHistory(userId, p, PER_PAGE)
        .then((r) => {
          setItems(r.items);
          setTotal(r.total);
        })
        .catch((e: unknown) => {
          setItems([]);
          setTotal(0);
          setErr(e instanceof Error ? e.message : "Не удалось загрузить историю");
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
    return <p className="up-muted">Подключений не найдено</p>;
  }

  return (
    <div className="up-tariffs">
      <table className="dt up-tariffs-table">
        <thead>
          <tr>
            <th className="up-tariffs-th-date">Подключение</th>
            <th className="up-tariffs-th-type">Тип</th>
            <th className="up-tariffs-th-date">Отключение</th>
            <th className="up-tariffs-th-amt">Цена</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={`${row.activated_at}-${row.row_kind}-${i}`}>
              <td className="up-tariffs-date">{row.activated_at_label}</td>
              <td className="up-tariffs-type">
                <span
                  className={typeBadgeClass(row)}
                  title={row.type_hint ?? undefined}
                >
                  {row.type_label}
                </span>
              </td>
              <td className="up-tariffs-until">
                {row.active_tariff ? (
                  <span className="up-tariffs-active">Активный тариф</span>
                ) : (
                  row.deactivation_at_label ?? "—"
                )}
              </td>
              <td className="up-tariffs-amt">{row.price_label}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {total > PER_PAGE ? (
        <div className="ch-pager up-tariffs-pager">
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
