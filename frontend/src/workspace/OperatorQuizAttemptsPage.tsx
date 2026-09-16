import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  fetchMyQuizAttemptsPage,
  type OperatorQuizAttemptItem,
  type OperatorQuizAttemptType,
  type OperatorQuizAttemptsPage,
} from "@/api/operatorQuizStats";
import { fetchOperatorQuizAttemptReview } from "@/api/operatorQuizReview";
import {
  AttemptRow,
  QuizAttemptsPager,
  QuizAttemptsSummaryBar,
  type ReviewState,
} from "@/workspace/QuizAttemptsShared";

const PER_PAGE = 20;

export default function OperatorQuizAttemptsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const attemptType = (searchParams.get("type") === "kb_topic"
    ? "kb_topic"
    : "daily_warmup") as OperatorQuizAttemptType;
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);

  const [data, setData] = useState<OperatorQuizAttemptsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [reviews, setReviews] = useState<Record<number, ReviewState>>({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setExpandedId(null);
    fetchMyQuizAttemptsPage(attemptType, page, PER_PAGE)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(e instanceof Error ? e.message : "Не удалось загрузить попытки");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [attemptType, page]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.per_page)) : 1;

  function setType(next: OperatorQuizAttemptType) {
    setSearchParams({ type: next, page: "1" });
  }

  function toggleAttempt(item: OperatorQuizAttemptItem) {
    const isOpening = expandedId !== item.attempt_id;
    setExpandedId(isOpening ? item.attempt_id : null);
    if (isOpening && !reviews[item.attempt_id]) {
      setReviews((prev) => ({ ...prev, [item.attempt_id]: { status: "loading" } }));
      fetchOperatorQuizAttemptReview(item.attempt_id)
        .then((review) => {
          setReviews((prev) => ({ ...prev, [item.attempt_id]: { status: "ready", data: review } }));
        })
        .catch((e: unknown) => {
          setReviews((prev) => ({
            ...prev,
            [item.attempt_id]: {
              status: "error",
              message: e instanceof Error ? e.message : "Не удалось загрузить ответы",
            },
          }));
        });
    }
  }

  return (
    <div className="tp on stats-page">
      <div className="pg stats-page__inner admin-attempts-page">
        <header className="stats-page__header">
          <Link to="/account" className="admin-attempts-back">
            ← Назад в профиль
          </Link>
          <h1 className="stats-page__title">Мои попытки тестов</h1>
        </header>

        <div className="stats-pane-tabs" role="tablist" aria-label="Тип теста">
          <button
            type="button"
            role="tab"
            aria-selected={attemptType === "daily_warmup"}
            className={`stats-pane-tab${attemptType === "daily_warmup" ? " on" : ""}`}
            onClick={() => setType("daily_warmup")}
          >
            Ежедневные тесты
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={attemptType === "kb_topic"}
            className={`stats-pane-tab${attemptType === "kb_topic" ? " on" : ""}`}
            onClick={() => setType("kb_topic")}
          >
            Тесты по базе знаний
          </button>
        </div>

        {data ? (
          <QuizAttemptsSummaryBar
            total={data.total}
            passedCount={data.passed_count}
            avgMistakes={data.avg_mistakes}
            avgScorePercent={data.avg_score_percent}
          />
        ) : null}

        {loading ? (
          <div className="stats-page__state">Загрузка…</div>
        ) : error ? (
          <div className="stats-page__state stats-page__state--error">{error}</div>
        ) : data && data.attempts.length > 0 ? (
          <>
            <div className="admin-attempts-list">
              {data.attempts.map((item) => (
                <AttemptRow
                  key={item.attempt_id}
                  item={item}
                  expanded={expandedId === item.attempt_id}
                  onToggle={() => toggleAttempt(item)}
                  reviewState={reviews[item.attempt_id]}
                />
              ))}
            </div>

            <QuizAttemptsPager
              page={page}
              totalPages={totalPages}
              onPageChange={(next) => setSearchParams({ type: attemptType, page: String(next) })}
            />
          </>
        ) : (
          <div className="stats-page__state">Попыток пока нет</div>
        )}
      </div>
    </div>
  );
}
