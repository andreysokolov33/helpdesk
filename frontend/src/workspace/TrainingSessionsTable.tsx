import type { TrainingSessionListItem } from "@/api/training";
import { quizScoreClass } from "@/api/statsQuizTraining";
import { quizScoreBarStyle } from "@/workspace/dailyQuizScore";
import {
  formatAnswerRatio,
  formatTrainingDay,
  formatTrainingDuration,
  trainingStatusKind,
  trainingStatusLabel,
} from "@/workspace/trainingFormat";

type Props = {
  items: TrainingSessionListItem[];
  compact?: boolean;
};

export default function TrainingSessionsTable({ items, compact = false }: Props) {
  return (
    <div className="stats-table-wrap">
      <table className={`dt stats-table trn-table${compact ? " trn-table--compact" : ""}`}>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Источник</th>
            <th className="trn-num">Ответы</th>
            <th>Результат</th>
            <th className="trn-num">Время</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => {
            const when = formatTrainingDay(s.started_at);
            const hasAnswers = s.total_answers > 0;
            return (
              <tr key={s.id}>
                <td>
                  <div className="trn-cell-main">{when.day}</div>
                  <div className="trn-cell-sub">{when.time}</div>
                </td>
                <td>
                  <div className="trn-cell-main trn-cell-ellipsis" title={s.source_title}>
                    {s.source_title}
                  </div>
                  <div className="trn-cell-sub">{s.source_kind_label}</div>
                </td>
                <td className="trn-num">
                  {hasAnswers ? (
                    <>
                      <span className="trn-ok-text">{s.correct_count}</span>
                      <span className="trn-cell-sub"> / {s.total_answers}</span>
                    </>
                  ) : (
                    "—"
                  )}
                </td>
                <td>
                  {hasAnswers ? (
                    <div className="trn-score-cell" title={formatAnswerRatio(s.correct_count, s.total_answers)}>
                      <span className={quizScoreClass(s.score_percent)}>{Math.round(s.score_percent)}%</span>
                      <span className="trn-minibar" aria-hidden>
                        <span style={quizScoreBarStyle(s.score_percent)} />
                      </span>
                    </div>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="trn-num">{formatTrainingDuration(s.duration_sec)}</td>
                <td>
                  <span className={`stats-status stats-status--${trainingStatusKind(s.status)}`}>
                    {trainingStatusLabel(s.status)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
