export type OperatorQuizOverallStats = {
  attempts_count: number;
  passed_count: number;
  avg_score_percent: number;
  articles_with_quiz?: number | null;
  articles_passed?: number | null;
};

export type OperatorQuizCategoryStat = {
  category_id: number;
  category_title: string;
  articles_with_quiz: number;
  articles_passed: number;
  articles_attempted: number;
  avg_score_percent: number;
  passed_attempts: number;
};

export type OperatorQuizAttemptItem = {
  attempt_id: number;
  attempt_type: string;
  finished_at: string | null;
  session_date: string | null;
  day_label: string;
  article_slug: string | null;
  article_title: string | null;
  category_title: string | null;
  correct_count: number;
  total_questions: number;
  score_percent: number;
  passed: boolean;
};

export type OperatorQuizStats = {
  eligible: boolean;
  kb_overall: OperatorQuizOverallStats;
  daily_overall: OperatorQuizOverallStats;
  categories: OperatorQuizCategoryStat[];
  kb_attempts: OperatorQuizAttemptItem[];
  daily_attempts: OperatorQuizAttemptItem[];
};

export async function fetchOperatorQuizStats(): Promise<OperatorQuizStats> {
  const res = await fetch("/api/v1/helpdesk/operators/me/quiz-stats", {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<OperatorQuizStats>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as OperatorQuizStats;
}

export function isOperatorQuizTrainee(me: { role?: string | null; level?: number | null }): boolean {
  return (me.role ?? "").toLowerCase() === "support" && me.level === 1;
}

export type OperatorQuizAttemptType = "daily_warmup" | "kb_topic";

export type OperatorQuizAttemptsPage = {
  attempt_type: OperatorQuizAttemptType;
  page: number;
  per_page: number;
  total: number;
  passed_count: number;
  avg_mistakes: number;
  avg_score_percent: number;
  attempts: OperatorQuizAttemptItem[];
};

export async function fetchMyQuizAttemptsPage(
  attemptType: OperatorQuizAttemptType,
  page: number,
  perPage: number,
): Promise<OperatorQuizAttemptsPage> {
  const q = new URLSearchParams({
    attempt_type: attemptType,
    page: String(page),
    per_page: String(perPage),
  });
  const res = await fetch(`/api/v1/helpdesk/operators/me/quiz-attempts?${q.toString()}`, {
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<OperatorQuizAttemptsPage>;
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return data as OperatorQuizAttemptsPage;
}
