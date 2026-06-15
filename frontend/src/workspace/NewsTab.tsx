import { useCallback, useEffect, useMemo, useState } from "react";
import OperatorNewsModal from "@/components/OperatorNewsModal";
import {
  fetchOperatorNewsDetail,
  fetchOperatorNewsHistory,
  formatNewsRelativeTime,
  markOperatorNewsRead,
  OPERATOR_NEWS_PAGE_SIZE,
  operatorNewsKindLabel,
  type OperatorNewsDetail,
  type OperatorNewsListItem,
} from "@/api/news";

function formatNewsDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function importanceLabel(importance: string): string | null {
  if (importance === "featured") return "Важно";
  if (importance === "important") return "Важно";
  return null;
}

export default function NewsTab() {
  const [items, setItems] = useState<OperatorNewsListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadTotal, setUnreadTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [detail, setDetail] = useState<OperatorNewsDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / OPERATOR_NEWS_PAGE_SIZE)),
    [total],
  );

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchOperatorNewsHistory({
      limit: OPERATOR_NEWS_PAGE_SIZE,
      offset: (page - 1) * OPERATOR_NEWS_PAGE_SIZE,
    })
      .then((data) => {
        if (!cancelled) {
          setItems(data.items);
          setTotal(data.total);
          setUnreadTotal(data.unread_total);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Не удалось загрузить новости");
          setItems([]);
          setTotal(0);
          setUnreadTotal(0);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page]);

  const openItem = useCallback(async (item: OperatorNewsListItem) => {
    setModalOpen(true);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const row = await fetchOperatorNewsDetail(item.id);
      setDetail(row);
      if (!row.is_read) {
        await markOperatorNewsRead(item.id);
        setItems((prev) =>
          prev.map((n) =>
            n.id === item.id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n,
          ),
        );
        setUnreadTotal((c) => Math.max(0, c - 1));
      }
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "Не удалось открыть новость");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  function closeModal() {
    setModalOpen(false);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(false);
  }

  function goToPage(next: number) {
    setPage(Math.min(Math.max(1, next), totalPages));
  }

  return (
    <div className="tp on news-page">
      <div className="pg">
        <div className="news-page__head">
          <div>
            <div className="news-page__title">Новости</div>
            <div className="news-page__sub">
              {loading
                ? "Загрузка…"
                : total > 0
                  ? `${total} ${total === 1 ? "публикация" : total < 5 ? "публикации" : "публикаций"}`
                  : "Пока нет новостей"}
              {!loading && unreadTotal > 0 ? ` · непрочитанных: ${unreadTotal}` : null}
            </div>
          </div>
        </div>

        {error ? <div className="news-page__error">{error}</div> : null}

        {!loading && !error && items.length === 0 ? (
          <div className="news-page__empty">Нет доступных новостей.</div>
        ) : null}

        {!loading && items.length > 0 ? (
          <div className="card news-page__card">
            <table className="dt news-table">
              <thead>
                <tr>
                  <th>Заголовок</th>
                  <th>Тип</th>
                  <th>Опубликована</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const kind = operatorNewsKindLabel(item.kind);
                  const imp = importanceLabel(item.importance);
                  return (
                    <tr
                      key={item.id}
                      className={`news-row${item.is_read ? "" : " news-row--unread"}`}
                      onClick={() => void openItem(item)}
                    >
                      <td className="news-row__title">
                        {!item.is_read ? <span className="news-row__dot" aria-hidden>●</span> : null}
                        {item.title}
                        {imp ? <span className={`tag ${item.importance === "featured" ? "thi" : "tn"}`}>{imp}</span> : null}
                      </td>
                      <td className="news-row__kind">{kind || "—"}</td>
                      <td className="news-row__date" title={formatNewsDate(item.published_at)}>
                        {formatNewsRelativeTime(item.published_at)}
                      </td>
                      <td className="news-row__status">
                        {item.is_read ? (
                          <span className="news-row__read" title={item.read_at ? formatNewsDate(item.read_at) : undefined}>
                            Прочитано
                          </span>
                        ) : (
                          <span className="news-row__unread">Новое</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {total > OPERATOR_NEWS_PAGE_SIZE ? (
              <div className="ch-pager news-page__pager">
                <button
                  type="button"
                  className="ch-page-btn"
                  disabled={page <= 1 || loading}
                  onClick={() => goToPage(page - 1)}
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
                  onClick={() => goToPage(page + 1)}
                >
                  Вперёд
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      <OperatorNewsModal
        open={modalOpen}
        detail={detail}
        loading={detailLoading}
        error={detailError}
        onClose={closeModal}
      />
    </div>
  );
}
