import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  fetchKbArticle,
  markKbArticleStudied,
  type KbArticleDetail,
  type KbQuizFinishResult,
} from "@/api/kb";
import { sanitizeKbHtml } from "@/utils/kbHtml";
import { bindKbReaderTabs } from "@/utils/kbReaderInteractions";
import { KbArticleStatusBadges } from "@/workspace/KbArticleStatusBadges";
import { KbArticleQuizCta } from "@/workspace/KbArticleQuizCta";
import { KbQuizPanel } from "@/workspace/KbQuizPanel";

type ArticleView = "article" | "quiz";

export default function KbArticlePage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const readerRef = useRef<HTMLElement>(null);
  const [article, setArticle] = useState<KbArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studiedMarked, setStudiedMarked] = useState(false);
  const [view, setView] = useState<ArticleView>("article");

  const openQuiz = useCallback(() => {
    setView("quiz");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const load = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    setView("article");
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
    if (!article || studiedMarked || view !== "article") return;

    const sentinel = document.getElementById("kb-article-end");
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
  }, [article, studiedMarked, view]);

  useEffect(() => {
    const root = readerRef.current;
    if (!root || view !== "article") return;
    return bindKbReaderTabs(root);
  }, [bodyHtml, view]);

  const handleQuizFinished = useCallback((result: KbQuizFinishResult) => {
    setArticle((prev) =>
      prev
        ? {
            ...prev,
            quiz_status: result.quiz_status,
            read_status: result.read_status,
            quiz_correct_count: result.correct_count,
            quiz_total_questions: result.total_questions,
            quiz_error_count: result.error_count,
            quiz_passed_at: result.quiz_passed_at,
            quiz_finished_at: result.quiz_finished_at,
          }
        : prev,
    );
    if (result.read_status === "read") {
      setStudiedMarked(true);
    }
  }, []);

  if (loading) {
    return (
      <div className="tp on kb-page">
        <div className="pg">
          <div className="kb-page__title">Загрузка…</div>
        </div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="tp on kb-page">
        <div className="pg">
          <button type="button" className="kb-back-btn" onClick={() => navigate("/kb")}>
            ← К базе знаний
          </button>
          <div className="kb-error">{error ?? "Статья не найдена"}</div>
        </div>
      </div>
    );
  }

  const quickAccess = Array.isArray(article.sidebar_json.quick_access)
    ? (article.sidebar_json.quick_access as { label?: string; anchor?: string }[])
    : [];

  return (
    <div className="tp on kb-page kb-article-page">
      <div className="pg kb-article-layout">
        <div className="kb-article-header">
          {article.subtitle ? (
            <div className="kb-article-header__subtitle">{article.subtitle}</div>
          ) : null}
          <div className="kb-article-header__title-row">
            <h1 className="kb-article-header__title">{article.title}</h1>
            <button type="button" className="kb-back-btn" onClick={() => navigate("/kb")}>
              ← К базе знаний
            </button>
          </div>
          <div className="kb-article-header__meta">
            <span className="kb-article-header__category">{article.category_title}</span>
            <KbArticleStatusBadges article={article} />
          </div>
        </div>

        {article.has_quiz ? (
          <div className="kb-article-view-tabs" role="tablist" aria-label="Режим просмотра">
            <button
              type="button"
              role="tab"
              aria-selected={view === "article"}
              className={`kb-article-view-tab${view === "article" ? " is-active" : ""}`}
              onClick={() => setView("article")}
            >
              Статья
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === "quiz"}
              className={`kb-article-view-tab${view === "quiz" ? " is-active" : ""}`}
              onClick={openQuiz}
            >
              Тестирование
            </button>
          </div>
        ) : null}

        <div className="kb-article-grid">
          <div className="kb-article-main">
            {view === "article" ? (
              <>
                <article
                  ref={readerRef}
                  className="kb-reader"
                  dangerouslySetInnerHTML={{ __html: bodyHtml }}
                />
                <div id="kb-article-end" className="kb-article-end" aria-hidden />
                {article.has_quiz ? (
                  <KbArticleQuizCta article={article} onStart={openQuiz} />
                ) : null}
              </>
            ) : (
              <KbQuizPanel
                slug={slug}
                onFinished={handleQuizFinished}
                onBackToArticle={() => setView("article")}
              />
            )}
          </div>
          {view === "article" && quickAccess.length > 0 ? (
            <aside className="kb-article-aside">
              <div className="kb-aside-card">
                <div className="kb-aside-card__title">Быстрый доступ</div>
                <nav className="kb-aside-nav">
                  {quickAccess.map((item) => (
                    <a
                      key={item.anchor ?? item.label}
                      className="kb-aside-nav__link"
                      href={`#${item.anchor ?? ""}`}
                    >
                      {item.label}
                    </a>
                  ))}
                </nav>
              </div>
            </aside>
          ) : null}
        </div>
      </div>
    </div>
  );
}
