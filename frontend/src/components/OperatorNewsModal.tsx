import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { OperatorNewsDetail } from "@/api/news";
import { sanitizeMessageHtml } from "@/utils/messageHtml";

type Props = {
  open: boolean;
  detail: OperatorNewsDetail | null;
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
};

export default function OperatorNewsModal({
  open,
  detail,
  loading = false,
  error = null,
  onClose,
}: Props) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const bodyHtml = detail?.body_html ? sanitizeMessageHtml(detail.body_html) : "";

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="operator-news-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="clf-box operator-news-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico operator-news-modal__ico" aria-hidden>
            🔔
          </div>
          <div>
            <div className="clf-hd-t" id="operator-news-title">
              {detail?.title || "Новость"}
            </div>
            {detail?.importance === "featured" || detail?.importance === "important" ? (
              <div className="clf-hd-sub operator-news-modal__importance">
                {detail.importance === "featured" ? "Важное оповещение" : "Важно"}
              </div>
            ) : null}
          </div>
        </div>
        <div className="clf-bd operator-news-modal__body">
          {loading ? <p className="op-admin-hint">Загрузка…</p> : null}
          {!loading && error ? <p className="op-admin-hint">{error}</p> : null}
          {!loading && !error && bodyHtml ? (
            <div className="operator-news-modal__html" dangerouslySetInnerHTML={{ __html: bodyHtml }} />
          ) : null}
          {!loading && !error && detail && !bodyHtml ? (
            <p className="op-admin-hint">Текст новости пуст.</p>
          ) : null}
        </div>
        <div className="clf-ft">
          {detail?.link_path ? (
            <button
              type="button"
              className="clf-btn pri"
              onClick={() => {
                onClose();
                navigate(detail.link_path!);
              }}
            >
              Перейти
            </button>
          ) : null}
          <button type="button" className="clf-btn sec" onClick={onClose}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
