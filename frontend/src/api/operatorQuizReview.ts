import type { KbQuizQuestion } from "@/api/kb";

export type OperatorQuizAnsweredReview = {
  question_id: number;
  selected_option_ids: number[];
  is_correct: boolean;
  correct_option_ids: number[];
  explanation: string | null;
};

export type OperatorQuizAttemptReview = {
  attempt_id: number;
  attempt_type: string;
  finished_at: string | null;
  session_date: string | null;
  article_slug: string | null;
  article_title: string | null;
  category_title: string | null;
  correct_count: number;
  total_questions: number;
  score_percent: number;
  passed: boolean;
  passing_score_percent: number;
  questions: KbQuizQuestion[];
  answered: OperatorQuizAnsweredReview[];
};

async function reviewJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchOperatorQuizAttemptReview(
  attemptId: number,
): Promise<OperatorQuizAttemptReview> {
  return reviewJson<OperatorQuizAttemptReview>(
    `/api/v1/helpdesk/operators/me/quiz-attempts/${attemptId}/review`,
  );
}

export async function startOperatorQuizPractice(
  sourceAttemptId: number,
): Promise<{ attempt_id: number; total_questions: number }> {
  return reviewJson(`/api/v1/helpdesk/operators/me/quiz-attempts/${sourceAttemptId}/practice`, {
    method: "POST",
  });
}
