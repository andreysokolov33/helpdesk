import type { KbQuizQuestion } from "@/api/kb";

export type TrainingSourceType = "daily" | "article";
export type TrainingSessionStatus = "in_progress" | "finished" | "abandoned";

export type TrainingArticleSource = {
  id: number;
  slug: string;
  title: string;
  questions_count: number;
};

export type TrainingCategorySource = {
  id: number;
  title: string;
  questions_count: number;
  articles: TrainingArticleSource[];
};

export type TrainingSources = {
  daily: { available: boolean; title: string; questions_count: number };
  all_articles: { questions_count: number; articles_count: number };
  categories: TrainingCategorySource[];
  inactivity_minutes: number;
};

export type TrainingSessionState = {
  id: number;
  source_type: TrainingSourceType;
  source_title: string;
  source_kind_label: string;
  article_id: number | null;
  category_id: number | null;
  status: TrainingSessionStatus;
  started_at: string;
  last_answer_at: string | null;
  finished_at: string | null;
  total_answers: number;
  correct_count: number;
  wrong_count: number;
  score_percent: number;
  duration_sec: number;
  inactivity_minutes: number;
};

export type TrainingNextQuestion = {
  session: TrainingSessionState;
  question: KbQuizQuestion | null;
  round_no: number;
  round_position: number;
  pool_size: number;
};

export type TrainingArticleLink = {
  id: number;
  slug: string;
  title: string;
};

export type TrainingAnswerResult = {
  is_correct: boolean;
  correct_option_ids: number[];
  explanation: string | null;
  article: TrainingArticleLink | null;
  completed: boolean;
  session: TrainingSessionState;
};

export type TrainingSessionListItem = {
  id: number;
  source_type: TrainingSourceType;
  source_title: string;
  source_kind_label: string;
  status: TrainingSessionStatus;
  started_at: string;
  last_answer_at: string | null;
  finished_at: string | null;
  total_answers: number;
  correct_count: number;
  wrong_count: number;
  score_percent: number;
  duration_sec: number;
};

export type TrainingTotals = {
  sessions_count: number;
  total_answers: number;
  correct_count: number;
  score_percent: number;
  total_duration_sec: number;
};

export type TrainingMySessions = {
  page: number;
  per_page: number;
  total: number;
  totals: TrainingTotals;
  items: TrainingSessionListItem[];
};

export type TrainingAdminSummary = {
  date_from: string;
  date_to: string;
  operators_count: number;
  active_operators_count: number;
  sessions_count: number;
  total_answers: number;
  correct_count: number;
  avg_score_percent: number;
  total_duration_sec: number;
  coverage: number;
};

export type TrainingLeaderItem = {
  rank: number;
  operator_id: number;
  operator_name: string;
  correct: number;
  total: number;
  raw_percent: number;
  score_percent: number;
  coverage: number;
  low_data: boolean;
};

export type TrainingLeaders = {
  date_from: string;
  date_to: string;
  k: number;
  p0_percent: number;
  low_data_threshold: number;
  items: TrainingLeaderItem[];
};

export type TrainingAdminOperatorRow = {
  operator_id: number;
  operator_name: string;
  sessions_count: number;
  total_answers: number;
  correct_count: number;
  score_percent: number | null;
  coverage: number;
  total_duration_sec: number;
  last_activity_at: string | null;
  has_active_session: boolean;
};

export type TrainingAdminOperators = {
  date_from: string;
  date_to: string;
  items: TrainingAdminOperatorRow[];
};

export type TrainingAdminOperatorSessions = {
  date_from: string;
  date_to: string;
  operator_id: number;
  operator_name: string;
  page: number;
  per_page: number;
  total: number;
  items: TrainingSessionListItem[];
};

export type TrainingPeriod = { dateFrom: string; dateTo: string };

const BASE = "/api/v1/helpdesk/training";

async function trainingJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: unknown; message?: string } & Partial<T>;
  if (!res.ok) {
    const msg =
      typeof data.detail === "string"
        ? data.detail
        : typeof data.message === "string"
          ? data.message
          : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

function periodQuery(period: TrainingPeriod, extra?: Record<string, string>): string {
  const q = new URLSearchParams(extra);
  if (period.dateFrom) q.set("date_from", period.dateFrom);
  if (period.dateTo) q.set("date_to", period.dateTo);
  return q.toString();
}

export function fetchTrainingSources(): Promise<TrainingSources> {
  return trainingJson(`${BASE}/sources`);
}

export async function fetchActiveTrainingSession(): Promise<TrainingSessionState | null> {
  const data = await trainingJson<{ session: TrainingSessionState | null }>(`${BASE}/sessions/active`);
  return data.session ?? null;
}

export function startTrainingSession(body: {
  source_type: TrainingSourceType;
  article_id?: number;
  category_id?: number;
  all_articles?: boolean;
}): Promise<TrainingSessionState> {
  return trainingJson(`${BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function fetchTrainingNextQuestion(sessionId: number): Promise<TrainingNextQuestion> {
  return trainingJson(`${BASE}/sessions/${sessionId}/next`);
}

export function submitTrainingAnswer(
  sessionId: number,
  questionId: number,
  selectedOptionIds: number[],
): Promise<TrainingAnswerResult> {
  return trainingJson(`${BASE}/sessions/${sessionId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_id: questionId, selected_option_ids: selectedOptionIds }),
  });
}

export function finishTrainingSession(sessionId: number): Promise<TrainingSessionState> {
  return trainingJson(`${BASE}/sessions/${sessionId}/finish`, { method: "POST" });
}

export function fetchTrainingSession(sessionId: number): Promise<TrainingSessionState> {
  return trainingJson(`${BASE}/sessions/${sessionId}`);
}

export function fetchMyTrainingSessions(page = 1, perPage = 20): Promise<TrainingMySessions> {
  const q = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  return trainingJson(`${BASE}/sessions?${q.toString()}`);
}

export function fetchTrainingAdminSummary(period: TrainingPeriod): Promise<TrainingAdminSummary> {
  return trainingJson(`${BASE}/admin/summary?${periodQuery(period)}`);
}

export function fetchTrainingAdminLeaders(period: TrainingPeriod): Promise<TrainingLeaders> {
  return trainingJson(`${BASE}/admin/leaders?${periodQuery(period)}`);
}

export function fetchTrainingAdminOperators(period: TrainingPeriod): Promise<TrainingAdminOperators> {
  return trainingJson(`${BASE}/admin/operators?${periodQuery(period)}`);
}

export function fetchTrainingAdminOperatorSessions(
  operatorId: number,
  period: TrainingPeriod,
  page = 1,
  perPage = 20,
): Promise<TrainingAdminOperatorSessions> {
  const q = periodQuery(period, { page: String(page), per_page: String(perPage) });
  return trainingJson(`${BASE}/admin/operators/${operatorId}/sessions?${q}`);
}

/** Ссылка на статью БЗ (открывается в новой вкладке). */
export function trainingArticleHref(slug: string): string {
  return `/kb/${encodeURIComponent(slug)}`;
}
