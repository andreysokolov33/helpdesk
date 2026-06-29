import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchKbArticle,
  markKbArticleStudied,
  type KbArticleDetail,
} from "@/api/kb";
import { sanitizeKbHtml } from "@/utils/kbHtml";
import { bindKbReaderInteractions } from "@/utils/kbReaderInteractions";

type Props = {
  slug: string;
  onClose: () => void;
};

export default function TicketKbArticleOverlay({ slug, onClose }: Props) {
  const readerRef = useRef<HTMLElement>(null);
  const [article, setArticle] = useState<KbArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studiedMarked, setStudiedMarked] = useState(false);

  const load = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKbArticle(slug);
      setArticle(data);
      setStudiedMarked(data.read_status === "read");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить статью");
      setArticle(null);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    void load();
  }, [load]);

  const bodyHtml = useMemo(
    () => (article ? sanitizeKbHtml(article.content_html) : ""),
    [article],
  );

  useEffect(() => {
    if (!article || studiedMarked) return;

    const sentinel = document.getElementById("tk-kb-article-end");
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        void markKbArticleStudied(article.id)
          .then(() => setStudiedMarked(true))
          .catch(() => {});
      },
      { threshold: 0.2 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [article, studiedMarked]);

  useEffect(() => {
    const root = readerRef.current;
    if (!root || !bodyHtml) return;
    return bindKbReaderInteractions(root);
  }, [bodyHtml]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="tk-cc-kb-overlay"
      role="dialog"
      aria-modal="false"
      aria-label={article?.title ?? "Статья базы знаний"}
    >
      <header className="tk-cc-kb-overlay__head">
        <div className="tk-cc-kb-overlay__head-text">
          {article?.category_title ? (
            <div className="tk-cc-kb-overlay__category">{article.category_title}</div>
          ) : null}
          <div className="tk-cc-kb-overlay__title">{article?.title ?? "Загрузка…"}</div>
        </div>
        <button
          type="button"
          className="tk-cc-kb-overlay__close"
          onClick={onClose}
          aria-label="Закрыть статью"
        >
          ×
        </button>
      </header>

      <div className="tk-cc-kb-overlay__body">
        {loading ? <div className="tk-cc-kb-overlay__status">Загрузка статьи…</div> : null}
        {error ? <div className="tk-cc-kb-overlay__error">{error}</div> : null}
        {!loading && !error && article ? (
          <>
            <article
              ref={readerRef}
              className="kb-reader tk-cc-kb-overlay__reader"
              dangerouslySetInnerHTML={{ __html: bodyHtml }}
            />
            <div id="tk-kb-article-end" className="kb-article-end" aria-hidden />
          </>
        ) : null}
      </div>
    </div>
  );
}
