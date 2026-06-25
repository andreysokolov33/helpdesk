import type {
  OperatorQuizCategoryStat,
  OperatorQuizOverallStats,
} from "@/api/operatorQuizStats";

export type QuizTrainingSummary = {
  operators_count: number;
  kb_avg_score_percent: number;
  articles_passed_ratio_percent: number;
  daily_avg_score_percent: number;
  daily_pass_rate_percent: number;
  needs_attention_count: number;
};

export type QuizTrainingOperatorRow = {
  operator_id: number;
  operator_name: string;
  kb_articles_with_quiz: number;
  kb_articles_passed: number;
  kb_avg_score_percent: number;
  daily_attempts_count: number;
  daily_passed_count: number;
  daily_avg_score_percent: number;
  today_daily_passed: boolean | null;
  today_daily_label: string;
  weak_category_title: string | null;
  needs_attention: boolean;
};

export type QuizTrainingWeakArticle = {
  article_id: number;
  article_title: string;
  article_slug: string | null;
  category_title: string | null;
  passed: boolean;
  score_percent: number;
};

export type QuizTrainingOperatorDetail = {
  operator_id: number;
  operator_name: string;
  eligible: boolean;
  kb_overall: OperatorQuizOverallStats;
  daily_overall: OperatorQuizOverallStats;
  categories: OperatorQuizCategoryStat[];
  weak_articles: QuizTrainingWeakArticle[];
};

export type QuizTrainingDashboard = {
  date_from: string;
  date_to: string;
  summary: QuizTrainingSummary;
  operators: QuizTrainingOperatorRow[];
  operator_detail: QuizTrainingOperatorDetail | null;
};

export async function fetchQuizTrainingStats(params: {
  dateFrom?: string;
  dateTo?: string;
  operatorId?: number | null;
}): Promise<QuizTrainingDashboard> {
  const q = new URLSearchParams();
  if (params.dateFrom) q.set("date_from", params.dateFrom);
  if (params.dateTo) q.set("date_to", params.dateTo);
  if (params.operatorId != null) q.set("operator_id", String(params.operatorId));

  const res = await fetch(`/api/v1/helpdesk/stats/quiz-training?${q.toString()}`, {
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as {
    detail?: string;
  } & Partial<QuizTrainingDashboard>;
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return data as QuizTrainingDashboard;
}

export function quizScoreTone(percent: number): "good" | "warn" | "bad" {
  if (percent >= 85) return "good";
  if (percent >= 70) return "warn";
  return "bad";
}

export function quizScoreClass(percent: number): string {
  return `stats-quiz-score stats-quiz-score--${quizScoreTone(percent)}`;
}

export type TrainingMetricCard = {
  label: string;
  value: string;
  valueClass?: string;
  hint?: string;
};

export function buildTrainingMetricCards(
  summary: QuizTrainingSummary,
): TrainingMetricCard[] {
  const pct = (v: number) => `${v.toFixed(0)}%`;
  return [
    {
      label: "Операторов на обучении",
      value: String(summary.operators_count),
      hint: "Операторы support level 1",
    },
    {
      label: "Средний балл БЗ",
      value: pct(summary.kb_avg_score_percent),
      valueClass: quizScoreClass(summary.kb_avg_score_percent),
      hint: "Средний балл по тестам базы знаний",
    },
    {
      label: "Статей сдано (ср.)",
      value: pct(summary.articles_passed_ratio_percent),
      valueClass: quizScoreClass(summary.articles_passed_ratio_percent),
      hint: "Доля сданных статей с тестами",
    },
    {
      label: "Ежедневные тесты",
      value: pct(summary.daily_avg_score_percent),
      valueClass: quizScoreClass(summary.daily_avg_score_percent),
      hint: "Средний балл ежедневных тестов за выбранный период",
    },
    {
      label: "Нужна коррекция",
      value: String(summary.needs_attention_count),
      valueClass:
        summary.needs_attention_count > 0 ? "stats-m-val stats-m-val--bad" : undefined,
      hint: "Операторы с низкими показателями",
    },
  ];
}
