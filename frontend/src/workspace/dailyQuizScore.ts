import type { CSSProperties } from "react";

export type QuizScoreCounts = {
  correct_count: number;
  total_questions: number;
};

/** Градиент кружка: 0/N — красный, середина — жёлтый, N/N — зелёный. */
export function dailyQuizScoreStyle(
  correct: number,
  total: number,
): CSSProperties {
  const ratio = total > 0 ? Math.max(0, Math.min(1, correct / total)) : 0;
  const hue = Math.round(ratio * 128);
  const light = 46 + ratio * 8;
  const light2 = 36 + ratio * 8;
  return {
    background: `linear-gradient(145deg, hsl(${hue} 78% ${light}%), hsl(${hue} 74% ${light2}%))`,
    boxShadow: `0 3px 10px hsla(${hue}, 70%, 38%, 0.38)`,
  };
}

export function formatDailyQuizScoreTitle(
  sessionDate: string,
  item: QuizScoreCounts,
  dateLabel?: string,
): string {
  const datePart =
    dateLabel ??
    (() => {
      try {
        const d = new Date(`${sessionDate}T12:00:00`);
        return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
      } catch {
        return sessionDate;
      }
    })();
  return `${datePart} · ${item.correct_count} из ${item.total_questions}`;
}
