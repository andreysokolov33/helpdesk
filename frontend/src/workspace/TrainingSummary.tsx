import type { CSSProperties } from "react";
import type { TrainingSessionState } from "@/api/training";
import { quizScoreHue } from "@/workspace/dailyQuizScore";
import { formatTrainingDuration, pluralRu } from "@/workspace/trainingFormat";

type Props = {
  session: TrainingSessionState;
  notice?: string | null;
  /** Пройдены все вопросы источника — показываем поздравление. */
  completed?: boolean;
  onRestart: () => void;
  onPickAnother: () => void;
  onHistory: () => void;
};

function verdict(total: number, percent: number): string {
  if (total === 0) return "Вы не ответили ни на один вопрос — попробуйте ещё раз.";
  if (percent >= 90) return "Отличная точность. Материал усвоен.";
  if (percent >= 75) return "Хороший результат. Разберите ошибки — и будет отлично.";
  if (percent >= 50) return "Половина пути. Перечитайте статьи по вопросам с ошибками.";
  return "Стоит вернуться к статьям и потренироваться ещё.";
}

export default function TrainingSummary({ session, notice, completed = false, onRestart, onPickAnother, onHistory }: Props) {
  const total = session.total_answers;
  const percent = Math.round(session.score_percent);
  const hue = quizScoreHue(percent);
  const ring = {
    "--trn-ring-pct": String(total > 0 ? percent : 0),
    "--trn-ring-hue": String(hue),
  } as CSSProperties;

  return (
    <div className="trn-summary">
      {notice ? <div className="trn-alert trn-alert--info">{notice}</div> : null}
      <div className="trn-summary__card">
        <div className="trn-ring" style={ring} role="img" aria-label={`Точность ${percent}%`}>
          <div className="trn-ring__inner">
            <span className="trn-ring__val">{total > 0 ? `${percent}%` : "—"}</span>
            <span className="trn-ring__cap">точность</span>
          </div>
        </div>
        <div className="trn-summary__body">
          {completed ? (
            <div className="trn-summary__badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" aria-hidden>
                <path d="m5 12.5 4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Все {total} {pluralRu(total, "вопрос", "вопроса", "вопросов")} пройдены
            </div>
          ) : null}
          <div className="trn-summary__source">
            {session.source_type === "daily"
              ? session.source_title
              : `${session.source_kind_label}: ${session.source_title}`}
          </div>
          <h2 className="trn-summary__title">
            {session.status === "abandoned"
              ? "Тренировка прервана"
              : completed
                ? "Тренировка пройдена"
                : "Тренировка завершена"}
          </h2>
          <p className="trn-summary__verdict">{verdict(total, percent)}</p>
          <dl className="trn-summary__grid">
            <div>
              <dt>Ответов</dt>
              <dd>{total}</dd>
            </div>
            <div className="trn-summary__good">
              <dt>Верно</dt>
              <dd>{session.correct_count}</dd>
            </div>
            <div className="trn-summary__bad">
              <dt>Неверно</dt>
              <dd>{session.wrong_count}</dd>
            </div>
            <div>
              <dt>Время</dt>
              <dd>{formatTrainingDuration(session.duration_sec)}</dd>
            </div>
          </dl>
          {total > 0 && session.duration_sec > 0 ? (
            <p className="trn-summary__pace">
              В среднем {Math.max(1, Math.round(session.duration_sec / total))}{" "}
              {pluralRu(Math.max(1, Math.round(session.duration_sec / total)), "секунда", "секунды", "секунд")} на вопрос
            </p>
          ) : null}
          <div className="trn-summary__actions">
            <button type="button" className="trn-btn trn-btn--primary" onClick={onRestart}>
              Пройти ещё раз
            </button>
            <button type="button" className="trn-btn trn-btn--ghost" onClick={onPickAnother}>
              Другой источник
            </button>
            <button type="button" className="trn-btn trn-btn--link" onClick={onHistory}>
              История тренировок
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
