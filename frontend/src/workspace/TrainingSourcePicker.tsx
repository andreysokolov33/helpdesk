import { useMemo, useState } from "react";
import type { TrainingSessionState, TrainingSources, TrainingSourceType } from "@/api/training";
import { formatClock, pluralRu, secondsSince } from "@/workspace/trainingFormat";

export type TrainingStartChoice = {
  source_type: TrainingSourceType;
  article_id?: number;
  category_id?: number;
  all_articles?: boolean;
};

type Props = {
  sources: TrainingSources | null;
  loading: boolean;
  error: string | null;
  activeSession: TrainingSessionState | null;
  startingKey: string | null;
  onStart: (choice: TrainingStartChoice, key: string) => void;
  onResume: () => void;
  onRetry: () => void;
};

function questionsLabel(n: number): string {
  return `${n} ${pluralRu(n, "вопрос", "вопроса", "вопросов")}`;
}

export default function TrainingSourcePicker({
  sources,
  loading,
  error,
  activeSession,
  startingKey,
  onStart,
  onResume,
  onRetry,
}: Props) {
  const [query, setQuery] = useState("");
  const [openCategoryId, setOpenCategoryId] = useState<number | null>(null);
  const [showSingle, setShowSingle] = useState(false);

  const q = query.trim().toLowerCase();
  const categories = useMemo(() => {
    if (!sources) return [];
    if (!q) return sources.categories;
    return sources.categories
      .map((c) => {
        const catMatch = c.title.toLowerCase().includes(q);
        const articles = catMatch ? c.articles : c.articles.filter((a) => a.title.toLowerCase().includes(q));
        return { ...c, articles };
      })
      .filter((c) => c.articles.length > 0);
  }, [sources, q]);

  if (loading) {
    return (
      <div className="trn-picker" aria-busy="true">
        <div className="trn-modes">
          <div className="trn-mode trn-skeleton" />
          <div className="trn-mode trn-skeleton" />
        </div>
        <div className="trn-cats">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="trn-cat trn-skeleton trn-skeleton--row" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="trn-state trn-state--error">
        <p>{error}</p>
        <button type="button" className="kb-quiz-btn-secondary" onClick={onRetry}>
          Повторить
        </button>
      </div>
    );
  }

  if (!sources) return null;

  const busy = startingKey != null;
  const daily = sources.daily;
  const allArticles = sources.all_articles;

  return (
    <div className="trn-picker">
      {activeSession ? (
        <div className="trn-resume" role="status">
          <div className="trn-resume__text">
            <div className="trn-resume__title">У вас есть незавершённая тренировка</div>
            <div className="trn-resume__meta">
              {activeSession.source_title} · {activeSession.total_answers}{" "}
              {pluralRu(activeSession.total_answers, "ответ", "ответа", "ответов")} · идёт{" "}
              {formatClock(secondsSince(activeSession.started_at, Date.now()))}
            </div>
          </div>
          <button type="button" className="trn-btn trn-btn--primary" onClick={onResume}>
            Продолжить
          </button>
        </div>
      ) : null}

      <div className="trn-modes">
        <button
          type="button"
          className="trn-mode trn-mode--daily"
          disabled={!daily.available || busy}
          onClick={() => onStart({ source_type: "daily" }, "daily")}
        >
          <span className="trn-mode__head">
          <span className="trn-mode__icon" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" strokeLinecap="round" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </span>
            <span className="trn-mode__title">{daily.title}</span>
          </span>
          <span className="trn-mode__body">
            <span className="trn-mode__desc">
              {daily.available
                ? `Вопросы ежедневного теста вперемешку: ${questionsLabel(daily.questions_count)}`
                : "Пул ежедневного теста пока не настроен"}
            </span>
          </span>
          <span className="trn-mode__cta">{startingKey === "daily" ? "Запуск…" : "Начать"}</span>
        </button>

        <button
          type="button"
          className="trn-mode trn-mode--all"
          disabled={allArticles.questions_count === 0 || busy}
          onClick={() => onStart({ source_type: "article", all_articles: true }, "all")}
        >
          <span className="trn-mode__head">
          <span className="trn-mode__icon" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v15H5.5A1.5 1.5 0 0 0 4 20.5z" />
              <path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H13v15h5.5a1.5 1.5 0 0 1 1.5 1.5z" />
            </svg>
          </span>
            <span className="trn-mode__title">Все тесты статей</span>
          </span>
          <span className="trn-mode__body">
            <span className="trn-mode__desc">
              {allArticles.questions_count > 0
                ? `Вопросы всех статей вперемешку: ${questionsLabel(allArticles.questions_count)} из ${allArticles.articles_count} ${pluralRu(allArticles.articles_count, "статьи", "статей", "статей")}`
                : "В базе знаний пока нет статей с тестами"}
            </span>
          </span>
          <span className="trn-mode__cta">{startingKey === "all" ? "Запуск…" : "Начать"}</span>
        </button>
      </div>

      <section className={`trn-single${showSingle ? " is-open" : ""}`}>
        <button
          type="button"
          className="trn-single__toggle"
          aria-expanded={showSingle}
          aria-controls="trn-single-body"
          onClick={() => setShowSingle((v) => !v)}
        >
          <svg className="trn-cat__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="m9 6 6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="trn-single__title">Отдельные статьи и разделы</span>
          <span className="trn-single__hint">Тренировка по одной статье или одному разделу</span>
        </button>

        {showSingle ? (
          <div id="trn-single-body" className="trn-single__body">
            <input
              type="search"
              className="kb-search trn-search"
              placeholder="Найти статью или раздел"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Поиск статьи или раздела"
            />
      {categories.length === 0 ? (
        <div className="trn-state">
          {q ? "Ничего не найдено — измените запрос." : "В базе знаний пока нет статей с тестами."}
        </div>
      ) : (
        <div className="trn-cats">
          {categories.map((cat) => {
            const open = q.length > 0 || openCategoryId === cat.id;
            const catKey = `cat-${cat.id}`;
            return (
              <section key={cat.id} className={`trn-cat${open ? " is-open" : ""}`}>
                <div className="trn-cat__head">
                  <button
                    type="button"
                    className="trn-cat__toggle"
                    aria-expanded={open}
                    onClick={() => setOpenCategoryId((prev) => (prev === cat.id ? null : cat.id))}
                  >
                    <svg className="trn-cat__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                      <path d="m9 6 6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span className="trn-cat__title">{cat.title}</span>
                    <span className="trn-cat__count">
                      {cat.articles.length} {pluralRu(cat.articles.length, "статья", "статьи", "статей")} ·{" "}
                      {questionsLabel(cat.questions_count)}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="trn-btn trn-btn--ghost"
                    disabled={busy}
                    onClick={() => onStart({ source_type: "article", category_id: cat.id }, catKey)}
                  >
                    {startingKey === catKey ? "Запуск…" : "Весь раздел"}
                  </button>
                </div>
                {open ? (
                  <ul className="trn-articles">
                    {cat.articles.map((a) => {
                      const key = `art-${a.id}`;
                      return (
                        <li key={a.id}>
                          <button
                            type="button"
                            className="trn-article"
                            disabled={busy}
                            onClick={() => onStart({ source_type: "article", article_id: a.id }, key)}
                          >
                            <span className="trn-article__title">{a.title}</span>
                            <span className="trn-article__meta">
                              {startingKey === key ? "Запуск…" : questionsLabel(a.questions_count)}
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </section>
            );
          })}
        </div>
      )}
          </div>
        ) : null}
      </section>
    </div>
  );
}
