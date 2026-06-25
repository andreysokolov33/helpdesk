export type KbReadStatus = "unread" | "reading" | "read";
export type KbQuizStatus = "none" | "not_started" | "in_progress" | "passed" | "failed";

export type KbArticleListItem = {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  summary: string | null;
  category_id: number;
  category_title: string;
  has_quiz: boolean;
  read_status: KbReadStatus;
  quiz_status: KbQuizStatus;
  quiz_correct_count: number | null;
  quiz_total_questions: number | null;
  quiz_error_count: number | null;
  quiz_passed_at: string | null;
  quiz_finished_at: string | null;
};

export type KbCategorySection = {
  id: number;
  title: string;
  slug: string | null;
  sort_order: number;
  articles: KbArticleListItem[];
};

export type KbHomeResponse = {
  categories: KbCategorySection[];
  total_articles: number;
};

export type KbSearchResponse = {
  query: string;
  items: KbArticleListItem[];
};

export type KbQuizOption = {
  id: number;
  option_text: string;
  sort_order: number;
};

export type KbQuizQuestion = {
  id: number;
  question_text: string;
  selection_mode: "single" | "multiple";
  sort_order: number;
  options: KbQuizOption[];
};

export type KbQuizAnsweredState = {
  question_id: number;
  selected_option_ids: number[];
  is_correct: boolean;
};

export type KbQuizSession = {
  quiz_id: number;
  article_id: number;
  title: string;
  passing_score_percent: number;
  attempt_id: number | null;
  attempt_status: "none" | "in_progress" | "finished";
  passed: boolean | null;
  score: number | null;
  total_questions: number;
  correct_count: number | null;
  questions: KbQuizQuestion[];
  answered: KbQuizAnsweredState[];
};

export type KbQuizFinishResult = {
  attempt_id: number;
  passed: boolean;
  score: number;
  total_questions: number;
  correct_count: number;
  error_count: number;
  quiz_status: KbQuizStatus;
  read_status: KbReadStatus;
  quiz_passed_at: string | null;
  quiz_finished_at: string | null;
};

export type KbQuizSubmitAnswerResult = {
  is_correct: boolean;
  explanation: string | null;
  correct_option_ids: number[];
};

export type KbArticleDetail = KbArticleListItem & {
  content_html: string;
  sidebar_json: Record<string, unknown>;
  quiz_id: number | null;
  published_at: string | null;
};

async function kbJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchKbHome(): Promise<KbHomeResponse> {
  return kbJson<KbHomeResponse>("/api/v1/helpdesk/kb");
}

export async function searchKbArticles(query: string): Promise<KbSearchResponse> {
  const sp = new URLSearchParams({ q: query });
  return kbJson<KbSearchResponse>(`/api/v1/helpdesk/kb/search?${sp}`);
}

export async function fetchKbArticle(slug: string): Promise<KbArticleDetail> {
  return kbJson<KbArticleDetail>(`/api/v1/helpdesk/kb/articles/${encodeURIComponent(slug)}`);
}

export async function markKbArticleStudied(articleId: number): Promise<void> {
  await kbJson(`/api/v1/helpdesk/kb/articles/${articleId}/studied`, { method: "POST" });
}

export async function fetchKbQuizSession(slug: string): Promise<KbQuizSession> {
  return kbJson<KbQuizSession>(
    `/api/v1/helpdesk/kb/articles/${encodeURIComponent(slug)}/quiz`,
  );
}

export async function startKbQuizAttempt(slug: string): Promise<{ attempt_id: number; total_questions: number }> {
  return kbJson(`/api/v1/helpdesk/kb/articles/${encodeURIComponent(slug)}/quiz/attempts`, {
    method: "POST",
  });
}

export async function submitKbQuizAnswer(
  attemptId: number,
  questionId: number,
  selectedOptionIds: number[],
): Promise<KbQuizSubmitAnswerResult> {
  return kbJson<KbQuizSubmitAnswerResult>(
    `/api/v1/helpdesk/kb/quiz-attempts/${attemptId}/answers`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: questionId,
        selected_option_ids: selectedOptionIds,
      }),
    },
  );
}

export async function finishKbQuizAttempt(attemptId: number): Promise<KbQuizFinishResult> {
  return kbJson<KbQuizFinishResult>(
    `/api/v1/helpdesk/kb/quiz-attempts/${attemptId}/finish`,
    { method: "POST" },
  );
}

export function kbReadStatusLabel(status: KbReadStatus): string {
  if (status === "read") return "Прочитано";
  if (status === "reading") return "Читаете";
  return "Не прочитано";
}

export function kbQuizStatusLabel(item: Pick<KbArticleListItem, "has_quiz" | "quiz_status" | "quiz_error_count" | "quiz_correct_count" | "quiz_total_questions">): string | null {
  if (!item.has_quiz || item.quiz_status === "none") return null;
  if (item.quiz_status === "passed") return "Тест сдан";
  if (item.quiz_status === "in_progress") return "Тест в процессе";
  if (item.quiz_status === "failed") {
    if (item.quiz_error_count != null && item.quiz_error_count > 0) {
      return `Тест: ошибок ${item.quiz_error_count}`;
    }
    if (item.quiz_correct_count != null && item.quiz_total_questions != null) {
      return `Тест: ${item.quiz_correct_count}/${item.quiz_total_questions}`;
    }
    return "Тест не сдан";
  }
  return "Тест не пройден";
}
