import { useCallback, useEffect, useState } from "react";
import {
  fetchUserPayments,
  type PaymentHistoryItem,
} from "@/api/userProfile";
import { fmtMoneyRu } from "@/utils/money";

const PER_PAGE = 10;

function payStateClass(state: string) {
  return `up-pay-badge up-pay-state up-pay-state--${state}`;
}

function payTypeClass(paymentType: string) {
  const key = paymentType.replace(/[^a-z0-9_-]/gi, "") || "unknown";
  return `up-pay-badge up-pay-type up-pay-type--${key}`;
}

type Props = {
  userId: number;
};

export default function PaymentsHistoryPanel({ userId }: Props) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<PaymentHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));

  const loadPage = useCallback(
    (p: number) => {
      setPage(p);
      setLoading(true);
      setErr(null);
      fetchUserPayments(userId, p, PER_PAGE)
        .then((r) => {
          setItems(r.items);
          setTotal(r.total);
        })
        .catch((e: unknown) => {
          setItems([]);
          setTotal(0);
          setErr(e instanceof Error ? e.message : "Не удалось загрузить платежи");
        })
        .finally(() => setLoading(false));
    },
    [userId],
  );

  useEffect(() => {
    loadPage(1);
  }, [loadPage]);

  if (loading && items.length === 0) {
    return <p className="up-muted">Загрузка платежей…</p>;
  }

  if (err) {
    return <p className="up-muted up-error">{err}</p>;
  }

  if (items.length === 0) {
    return <p className="up-muted">Платежей не найдено</p>;
  }

  return (
    <div className="up-payments">
      <table className="dt up-payments-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Статус</th>
            <th>Система</th>
            <th className="up-payments-th-amt">Сумма</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={`${row.msk_date}-${row.state}-${row.payment_type}-${row.amount}-${i}`}>
              <td className="up-payments-date">{row.msk_date_label}</td>
              <td>
                <span className={payStateClass(row.state)}>{row.state_label}</span>
              </td>
              <td>
                <span className={payTypeClass(row.payment_type)}>{row.type_label}</span>
              </td>
              <td className="up-payments-amt">{fmtMoneyRu(row.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {total > PER_PAGE ? (
        <div className="ch-pager up-payments-pager">
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
