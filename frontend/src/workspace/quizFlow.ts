import type { KbQuizAnsweredState, KbQuizQuestion } from "@/api/kb";

export type QuizAnswerFeedback = {
  is_correct: boolean;
  explanation: string | null;
  correct_option_ids: number[];
  selectedOptionIds: number[];
};

type AnsweredSession = {
  answered: KbQuizAnsweredState[];
  questions: KbQuizQuestion[];
};

export function firstUnansweredIndex(session: AnsweredSession): number {
  const answeredIds = new Set(session.answered.map((a) => Number(a.question_id)));
  const idx = session.questions.findIndex((q) => !answeredIds.has(Number(q.id)));
  return idx === -1 ? session.questions.length : idx;
}

export function feedbackFromAnswered(
  session: AnsweredSession,
  questionId: number,
): QuizAnswerFeedback | null {
  const entry = session.answered.find((a) => Number(a.question_id) === Number(questionId));
  if (!entry) return null;
  const correctIds =
    entry.correct_option_ids && entry.correct_option_ids.length > 0
      ? entry.correct_option_ids
      : entry.is_correct
        ? [...entry.selected_option_ids]
        : [];
  return {
    is_correct: entry.is_correct,
    explanation: null,
    correct_option_ids: correctIds,
    selectedOptionIds: [...entry.selected_option_ids],
  };
}

export function isAlreadyAnsweredError(message: string): boolean {
  return /уже дан ответ/i.test(message);
}
