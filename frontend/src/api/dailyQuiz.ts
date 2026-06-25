import type {
  KbQuizAnsweredState,
  KbQuizFinishResult,
  KbQuizQuestion,
  KbQuizSubmitAnswerResult,
} from "@/api/kb";

export type DailyQuizHistoryItem = {
  session_date: string;
  day_label: string;
  passed: boolean | null;
  status: string;
  correct_count: number;
  total_questions: number;
};

export type DailyQuizStatus = {
  required: boolean;
  show_modal: boolean;
  session_date: string | null;
  attempt_id: number | null;
  attempt_status: "none" | "in_progress" | "finished";
  title: string | null;
  questions_per_session: number | null;
  history: DailyQuizHistoryItem[];
};

export type DailyQuizSession = {
  quiz_id: number;
  article_id: number;
  title: string;
  passing_score_percent: number;
  session_date: string;
  attempt_id: number | null;
  attempt_status: "none" | "in_progress" | "finished";
  passed: boolean | null;
  total_questions: number;
  correct_count: number | null;
  questions: KbQuizQuestion[];
  answered: KbQuizAnsweredState[];
};

async function dailyJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchDailyQuizStatus(): Promise<DailyQuizStatus> {
  return dailyJson<DailyQuizStatus>("/api/v1/helpdesk/daily-quiz/status");
}

export async function fetchDailyQuizSession(): Promise<DailyQuizSession> {
  return dailyJson<DailyQuizSession>("/api/v1/helpdesk/daily-quiz/session");
}

export async function startDailyQuizAttempt(): Promise<{ attempt_id: number; total_questions: number }> {
  return dailyJson("/api/v1/helpdesk/daily-quiz/attempts", { method: "POST" });
}

export async function submitDailyQuizAnswer(
  attemptId: number,
  questionId: number,
  selectedOptionIds: number[],
): Promise<KbQuizSubmitAnswerResult> {
  return dailyJson(`/api/v1/helpdesk/daily-quiz/quiz-attempts/${attemptId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question_id: questionId,
      selected_option_ids: selectedOptionIds,
    }),
  });
}

export async function finishDailyQuizAttempt(attemptId: number): Promise<KbQuizFinishResult> {
  return dailyJson(`/api/v1/helpdesk/daily-quiz/quiz-attempts/${attemptId}/finish`, {
    method: "POST",
  });
}
