import type { OperatorQuizAttemptItem } from "@/api/operatorQuizStats";
import type { OperatorQuizAttemptReview } from "@/api/operatorQuizReview";

export type AdminQuizAttemptType = "daily_warmup" | "kb_topic";

export type AdminQuizAttemptsPage = {
  operator_id: number;
  operator_name: string;
  attempt_type: AdminQuizAttemptType;
  page: number;
  per_page: number;
  total: number;
  passed_count: number;
  avg_mistakes: number;
  avg_score_percent: number;
  attempts: OperatorQuizAttemptItem[];
};

async function jsonOrThrow<T>(res: Response): Promise<T> {
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return data as T;
}

export async function fetchAdminQuizAttemptsPage(
  operatorId: number,
  attemptType: AdminQuizAttemptType,
  page: number,
  perPage: number,
): Promise<AdminQuizAttemptsPage> {
  const q = new URLSearchParams({
    attempt_type: attemptType,
    page: String(page),
    per_page: String(perPage),
  });
  const res = await fetch(
    `/api/v1/helpdesk/stats/quiz-training/operators/${operatorId}/attempts?${q.toString()}`,
    { credentials: "include" },
  );
  return jsonOrThrow<AdminQuizAttemptsPage>(res);
}

export async function fetchAdminQuizAttemptReview(
  operatorId: number,
  attemptId: number,
): Promise<OperatorQuizAttemptReview> {
  const res = await fetch(
    `/api/v1/helpdesk/stats/quiz-training/operators/${operatorId}/attempts/${attemptId}/review`,
    { credentials: "include" },
  );
  return jsonOrThrow<OperatorQuizAttemptReview>(res);
}
