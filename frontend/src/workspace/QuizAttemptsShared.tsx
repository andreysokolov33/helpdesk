import { Link } from "react-router-dom";
import type { OperatorQuizAttemptItem } from "@/api/operatorQuizStats";
import type { OperatorQuizAttemptReview } from "@/api/operatorQuizReview";
import { quizScoreClass } from "@/api/statsQuizTraining";
import { dailyQuizScoreStyle } from "@/workspace/dailyQuizScore";

export type ReviewState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: OperatorQuizAttemptReview };

export function formatAttemptDate(item: {
  session_date: string | null;
  finished_at: string | null;
}): string {
  const raw = item.session_date ?? item.finished_at;
  if (!raw) return "—";
  try {
    const iso = item.session_date ? `${item.session_date}T12:00:00` : raw;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

export function AttemptQuestions({ review }: { review: OperatorQuizAttemptReview }) {
  return (
    <div className="admin-attempt-card__questions">
      {review.questions.map((q, qIdx) => {
        const entry = review.answered.find((a) => Number(a.question_id) === Number(q.id));
        const selectedIds = entry?.selected_option_ids ?? [];
        const correctIds = entry?.correct_option_ids ?? [];
        return (
          <div key={q.id} className="qblock answered admin-attempt-question">
            <div className="q-text">
              {qIdx + 1}. {q.question_text}
            </div>
            <div className="q-opts">
              {q.options.map((opt, optIdx) => {
                const letter = String.fromCharCode(65 + optIdx);
                const isSelected = selectedIds.includes(opt.id);
                const isCorrect = correctIds.includes(opt.id);
                let stateClass = "";
                if (isCorrect) stateClass = "correct";
                else if (isSelected) stateClass = "wrong";
                return (
                  <div key={opt.id} className={`opt${stateClass ? ` ${stateClass}` : ""}`}>
                    <span className="om">{letter}</span>
                    <span>{opt.option_text}</span>
                    {isSelected ? <span className="admin-attempt-picked">выбрано</span> : null}
                  </div>
                );
              })}
            </div>
            {entry?.explanation ? (
              <div className="q-expl show">
                <strong>Разбор:</strong> {entry.explanation}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export function AttemptRow({
  item,
  expanded,
  onToggle,
  reviewState,
}: {
  item: OperatorQuizAttemptItem;
  expanded: boolean;
  onToggle: () => void;
  reviewState: ReviewState | undefined;
}) {
  const title =
    item.article_title ?? (item.attempt_type === "daily_warmup" ? "Ежедневный тест" : "Тест по статье");

  return (
    <div className={`admin-attempt-card${expanded ? " is-expanded" : ""}`}>
      <button type="button" className="admin-attempt-row" onClick={onToggle} aria-expanded={expanded}>
        <span className="admin-attempt-row__icon" aria-hidden>
          {expanded ? "▾" : "▸"}
        </span>
        <span className="admin-attempt-row__date">{formatAttemptDate(item)}</span>
        <span className="admin-attempt-row__title">{title}</span>
        {item.category_title ? (
          <span className="admin-attempt-row__category">{item.category_title}</span>
        ) : null}
        <span className="admin-attempt-row__spacer" />
        {item.article_slug ? (
          <Link
            to={`/kb/${item.article_slug}`}
            className="admin-attempt-card__kb-link"
            onClick={(e) => e.stopPropagation()}
            title="Открыть статью"
          >
            К статье →
          </Link>
        ) : null}
        <span
          className="op-quiz-score-badge admin-attempt-row__badge"
          style={dailyQuizScoreStyle(item.correct_count, item.total_questions)}
          title={`${item.score_percent}%`}
        >
          {item.correct_count}/{item.total_questions}
        </span>
        <span className={`op-quiz-pass-tag${item.passed ? " is-pass" : " is-fail"}`}>
          {item.passed ? "Сдан" : "Не сдан"}
        </span>
      </button>

      {expanded ? (
        <div className="admin-attempt-card__body">
          {!reviewState || reviewState.status === "loading" ? (
            <div className="stats-page__state">Загрузка ответов…</div>
          ) : reviewState.status === "error" ? (
            <div className="stats-page__state stats-page__state--error">{reviewState.message}</div>
          ) : (
            <AttemptQuestions review={reviewState.data} />
          )}
        </div>
      ) : null}
    </div>
  );
}

export function QuizAttemptsSummaryBar({
  total,
  passedCount,
  avgMistakes,
  avgScorePercent,
}: {
  total: number;
  passedCount: number;
  avgMistakes: number;
  avgScorePercent: number;
}) {
  const passRate = total > 0 ? (passedCount / total) * 100 : 0;
  return (
    <div className="admin-attempts-summary">
      <div className="stats-m-card">
        <div className="stats-m-label">Всего попыток</div>
        <div className="stats-m-val">{total}</div>
      </div>
      <div className="stats-m-card">
        <div className="stats-m-label">Сдано</div>
        <div className={`stats-m-val ${quizScoreClass(passRate)}`}>
          {passedCount} / {total}
        </div>
        <div className="admin-attempts-summary__hint">{passRate.toFixed(0)}% успешных</div>
      </div>
      <div className="stats-m-card">
        <div className="stats-m-label">Средний балл</div>
        <div className={`stats-m-val ${quizScoreClass(avgScorePercent)}`}>
          {avgScorePercent.toFixed(0)}%
        </div>
      </div>
      <div className="stats-m-card">
        <div className="stats-m-label">Ошибок в среднем за тест</div>
        <div className="stats-m-val">{avgMistakes.toFixed(2)}</div>
      </div>
    </div>
  );
}

export function QuizAttemptsPager({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="admin-attempts-pager">
      <button
        type="button"
        className="kb-quiz-btn-secondary"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Назад
      </button>
      <span className="admin-attempts-pager__label">
        Страница {page} из {totalPages}
      </span>
      <button
        type="button"
        className="kb-quiz-btn-secondary"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Вперёд →
      </button>
    </div>
  );
}
