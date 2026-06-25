import type { KbArticleListItem } from "@/api/kb";
import { formatQuizCompletedAt } from "@/utils/dateTime";

type Props = {
  article: Pick<
    KbArticleListItem,
    | "quiz_status"
    | "quiz_correct_count"
    | "quiz_total_questions"
    | "quiz_error_count"
    | "quiz_passed_at"
    | "quiz_finished_at"
  >;
  onStart: () => void;
};

function quizStatusLine(article: Props["article"]): { text: string; tone: "ok" | "fail" | "muted" } {
  if (article.quiz_status === "passed") {
    return { text: "Тест сдан", tone: "ok" };
  }
  if (article.quiz_status === "failed") {
    const errors = article.quiz_error_count;
    if (errors != null && errors > 0) {
      return { text: `Тест не сдан · ошибок: ${errors}`, tone: "fail" };
    }
    return { text: "Тест не сдан", tone: "fail" };
  }
  if (article.quiz_status === "in_progress") {
    return { text: "Тест в процессе", tone: "muted" };
  }
  return { text: "Тест не пройден", tone: "muted" };
}

function quizCompletedAt(article: Props["article"]): string | null {
  const iso =
    article.quiz_status === "passed"
      ? article.quiz_passed_at ?? article.quiz_finished_at
      : article.quiz_status === "failed"
        ? article.quiz_finished_at
        : null;
  const formatted = formatQuizCompletedAt(iso);
  return formatted || null;
}

function quizButtonLabel(quizStatus: KbArticleListItem["quiz_status"]): string {
  if (quizStatus === "failed") return "Пройти тестирование снова";
  if (quizStatus === "passed") return "Открыть тест";
  if (quizStatus === "in_progress") return "Продолжить тестирование";
  return "Пройти тестирование";
}

export function KbArticleQuizCta({ article, onStart }: Props) {
  const status = quizStatusLine(article);
  const completedAt = quizCompletedAt(article);

  return (
    <div className="kb-article-quiz-cta">
      <div className={`kb-article-quiz-cta__status kb-article-quiz-cta__status--${status.tone}`}>
        {status.text}
      </div>
      {completedAt ? (
        <div className="kb-article-quiz-cta__date">Завершён: {completedAt}</div>
      ) : null}
      <button type="button" className="btn-main" onClick={onStart}>
        {quizButtonLabel(article.quiz_status)}
      </button>
    </div>
  );
}
