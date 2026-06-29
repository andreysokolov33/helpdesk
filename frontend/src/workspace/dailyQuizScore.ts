import type { CSSProperties } from "react";

export type QuizScoreCounts = {
  correct_count: number;
  total_questions: number;
};

export function quizScoreHue(percent: number): number {
  const ratio = Math.max(0, Math.min(1, percent / 100));
  return Math.round(ratio * 128);
}

/** Пастельный кружок: оттенок задаётся hue (0 — красный, середина — жёлтый, 100% — зелёный). */
export function dailyQuizScoreStyle(
  correct: number,
  total: number,
): CSSProperties {
  const percent = total > 0 ? (correct / total) * 100 : 0;
  return {
    "--quiz-score-hue": String(quizScoreHue(percent)),
  } as CSSProperties;
}

export function quizScoreBarStyle(percent: number): CSSProperties {
  const hue = quizScoreHue(percent);
  return {
    width: `${Math.max(0, Math.min(100, percent))}%`,
    background: `linear-gradient(90deg, hsl(${hue} 78% 52%), hsl(${hue} 74% 42%))`,
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
