import { Fragment } from "react";
import type { OperatorQuizAttemptItem } from "@/api/operatorQuizStats";
import {
  dailyQuizScoreStyle,
  formatDailyQuizScoreTitle,
} from "@/workspace/dailyQuizScore";

type Props = {
  items: OperatorQuizAttemptItem[];
  onSelect: (attemptId: number) => void;
  selectedId?: number | null;
  emptyMessage?: string;
};

function chainTitle(item: OperatorQuizAttemptItem): string {
  const scorePart = `${item.correct_count} из ${item.total_questions}`;
  if (item.session_date) {
    const datePart = formatDailyQuizScoreTitle(item.session_date, item, item.day_label);
    return datePart;
  }
  const title = item.article_title ?? "Тест";
  const dateRaw = item.finished_at;
  let datePart = item.day_label;
  if (dateRaw) {
    try {
      const d = new Date(dateRaw);
      if (!Number.isNaN(d.getTime())) {
        datePart = d.toLocaleDateString("ru-RU", {
          day: "numeric",
          month: "short",
          year: "numeric",
        });
      }
    } catch {
      // keep day_label
    }
  }
  const meta = item.category_title ? ` · ${item.category_title}` : "";
  return `${title}${meta} · ${datePart} · ${scorePart}`;
}

export default function QuizAttemptDotChain({
  items,
  onSelect,
  selectedId,
  emptyMessage = "Пока нет завершённых тестов",
}: Props) {
  if (items.length === 0) {
    return <div className="op-quiz-muted">{emptyMessage}</div>;
  }

  return (
    <div className="op-quiz-chain" aria-label="История тестов">
      <div className="op-quiz-chain__track">
        {items.map((item, index) => (
          <Fragment key={item.attempt_id}>
            {index > 0 ? <span className="op-quiz-chain__stem" aria-hidden /> : null}
            <span
              role="button"
              tabIndex={0}
              className={`op-quiz-chain__dot${selectedId === item.attempt_id ? " is-active" : ""}`}
              style={dailyQuizScoreStyle(item.correct_count, item.total_questions)}
              title={chainTitle(item)}
              aria-label={chainTitle(item)}
              aria-pressed={selectedId === item.attempt_id}
              onClick={() => onSelect(item.attempt_id)}
              onKeyDown={(e) => {
                if (e.key !== "Enter" && e.key !== " ") return;
                e.preventDefault();
                onSelect(item.attempt_id);
              }}
            >
              {item.day_label}
            </span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}
