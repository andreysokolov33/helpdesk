import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchKbQuizSession,
  finishKbQuizAttempt,
  startKbQuizAttempt,
  submitKbQuizAnswer,
  type KbQuizFinishResult,
  type KbQuizQuestion,
  type KbQuizSession,
} from "@/api/kb";
import {
  feedbackFromAnswered,
  firstUnansweredIndex,
  isAlreadyAnsweredError,
  type QuizAnswerFeedback,
} from "@/workspace/quizFlow";

type Props = {
  slug: string;
  onFinished: (result: KbQuizFinishResult) => void;
  onBackToArticle: () => void;
};

type AnswerFeedback = QuizAnswerFeedback;

function applySessionProgress(
  data: KbQuizSession,
  setters: {
    setSession: (v: KbQuizSession) => void;
    setAttemptId: (v: number | null) => void;
    setQuestionIndex: (v: number) => void;
    setFeedback: (v: AnswerFeedback | null) => void;
    setMultipleSelected: (v: number[]) => void;
  },
): number {
  setters.setSession(data);
  setters.setAttemptId(data.attempt_id);
  const idx = firstUnansweredIndex(data);
  setters.setQuestionIndex(idx);
  setters.setMultipleSelected([]);
  if (idx < data.questions.length) {
    setters.setFeedback(feedbackFromAnswered(data, data.questions[idx].id));
  } else {
    setters.setFeedback(null);
  }
  return idx;
}

export function KbQuizPanel({ slug, onFinished, onBackToArticle }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<KbQuizSession | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [finishResult, setFinishResult] = useState<KbQuizFinishResult | null>(null);
  const [multipleSelected, setMultipleSelected] = useState<number[]>([]);
  const [finishing, setFinishing] = useState(false);

  const syncFromSession = useCallback(
    (data: KbQuizSession) =>
      applySessionProgress(data, {
        setSession,
        setAttemptId,
        setQuestionIndex,
        setFeedback,
        setMultipleSelected,
      }),
    [],
  );

  const finishAttempt = useCallback(
    async (id: number) => {
      const result = await finishKbQuizAttempt(id);
      setFinishResult(result);
      onFinished(result);
    },
    [onFinished],
  );

  const bootstrap = useCallback(async () => {
    setLoading(true);
    setError(null);
    setFeedback(null);
    setFinishResult(null);
    setMultipleSelected([]);
    try {
      const data = await fetchKbQuizSession(slug);
      setSession(data);

      if (data.attempt_status === "finished") {
        setAttemptId(data.attempt_id);
        setQuestionIndex(data.questions.length);
        setLoading(false);
        return;
      }

      if (data.attempt_status === "in_progress" && data.attempt_id) {
        const idx = syncFromSession(data);
        if (idx >= data.questions.length) {
          await finishAttempt(data.attempt_id);
        }
        setLoading(false);
        return;
      }

      const started = await startKbQuizAttempt(slug);
      setAttemptId(started.attempt_id);
      setQuestionIndex(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить тест");
    } finally {
      setLoading(false);
    }
  }, [slug, finishAttempt, syncFromSession]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const totalQuestions = session?.questions.length ?? 0;
  const currentQuestion: KbQuizQuestion | null =
    session && questionIndex < totalQuestions ? session.questions[questionIndex] : null;

  const progressPct = useMemo(() => {
    if (!totalQuestions) return 0;
    if (finishResult || session?.attempt_status === "finished") return 100;
    return Math.round((questionIndex / totalQuestions) * 100);
  }, [finishResult, questionIndex, session?.attempt_status, totalQuestions]);

  const showFinished =
    finishResult != null ||
    (session?.attempt_status === "finished" && questionIndex >= totalQuestions);

  const passed = finishResult?.passed ?? session?.passed ?? false;
  const correctCount = finishResult?.correct_count ?? session?.correct_count ?? 0;
  const errorCount =
    finishResult?.error_count ??
    (session?.total_questions != null && session.correct_count != null
      ? session.total_questions - session.correct_count
      : 0);

  const submitAnswer = async (selectedOptionIds: number[]) => {
    if (!currentQuestion || !attemptId || feedback || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await submitKbQuizAnswer(
        attemptId,
        currentQuestion.id,
        [...selectedOptionIds].sort((a, b) => a - b),
      );
      setFeedback({ ...result, selectedOptionIds });
      setMultipleSelected([]);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось отправить ответ";
      if (isAlreadyAnsweredError(message) && session) {
        try {
          const fresh = await fetchKbQuizSession(slug);
          const idx = syncFromSession(fresh);
          if (idx >= fresh.questions.length && fresh.attempt_id) {
            await finishAttempt(fresh.attempt_id);
          }
          return;
        } catch {
          // fall through
        }
      }
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSingleSelect = async (optionId: number) => {
    await submitAnswer([optionId]);
  };

  const handleMultipleSubmit = async () => {
    if (multipleSelected.length === 0) return;
    await submitAnswer(multipleSelected);
  };

  const handleNext = async () => {
    if (!session || !attemptId || finishing) return;
    const isLast = questionIndex + 1 >= totalQuestions;
    if (isLast) {
      setFinishing(true);
      try {
        await finishAttempt(attemptId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Не удалось завершить тест");
      } finally {
        setFinishing(false);
      }
      return;
    }
    const nextIndex = questionIndex + 1;
    setQuestionIndex(nextIndex);
    setFeedback(null);
    setMultipleSelected([]);
    const nextQuestion = session.questions[nextIndex];
    if (nextQuestion) {
      const restored = feedbackFromAnswered(session, nextQuestion.id);
      if (restored) setFeedback(restored);
    }
  };

  const handleRetry = async () => {
    try {
      setLoading(true);
      setError(null);
      const started = await startKbQuizAttempt(slug);
      const data = await fetchKbQuizSession(slug);
      setSession(data);
      setAttemptId(started.attempt_id);
      setQuestionIndex(0);
      setFeedback(null);
      setFinishResult(null);
      setMultipleSelected([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось начать тест заново");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="kb-quiz-loading">Загрузка теста…</div>;
  }

  if (error && !session) {
    return (
      <div className="kb-quiz-error">
        <p>{error}</p>
        <button type="button" className="kb-quiz-btn-secondary" onClick={() => void bootstrap()}>
          Повторить
        </button>
      </div>
    );
  }

  if (!session) return null;

  return (
    <div className="quiz-wrap kb-quiz-wrap">
      <div className="quiz-hdr">
        <span className="quiz-badge">Тестирование</span>
        <span className="quiz-title">{session.title}</span>
      </div>

      <div className="quiz-progress-text">
        {showFinished
          ? "Тестирование завершено"
          : `Вопрос ${questionIndex + 1} из ${totalQuestions}${
              currentQuestion?.selection_mode === "multiple" && !feedback
                ? " · можно выбрать несколько вариантов"
                : ""
            }`}
      </div>
      <div className="quiz-progress-wrap" aria-hidden>
        <div className="quiz-progress-bar" style={{ width: `${progressPct}%` }} />
      </div>

      {error ? <div className="kb-quiz-inline-error">{error}</div> : null}

      {showFinished ? (
        <div className={`quiz-score-box show`}>
          <div className={`qs-num${passed ? "" : " qs-num--fail"}`}>
            {passed ? "Тест сдан" : "Тест не сдан"}
          </div>
          <p className="kb-quiz-score-summary">
            Вы ответили правильно на <strong>{correctCount}</strong> из{" "}
            <strong>{totalQuestions}</strong> вопросов.
            <br />
            Ошибок: <strong>{errorCount}</strong>.
          </p>
          <p className="kb-quiz-praise">
            {passed
              ? "Отличный результат! Материал темы успешно усвоен."
              : "Перечитайте статью и попробуйте снова."}
          </p>
          <div className="kb-quiz-score-actions">
            <button type="button" className="kb-quiz-btn-secondary" onClick={onBackToArticle}>
              К статье
            </button>
            {!passed ? (
              <button type="button" className="btn-next" onClick={() => void handleRetry()}>
                Пройти снова
              </button>
            ) : null}
          </div>
        </div>
      ) : currentQuestion ? (
        <div className={`qblock${feedback ? " answered" : ""}`}>
          <div className="q-text">{currentQuestion.question_text}</div>
          <div className="q-opts">
            {currentQuestion.options.map((opt, optIdx) => {
              const letter = String.fromCharCode(65 + optIdx);
              const isSelected = feedback
                ? feedback.selectedOptionIds.includes(opt.id)
                : multipleSelected.includes(opt.id);
              const isCorrect = feedback?.correct_option_ids.includes(opt.id);
              let stateClass = "";
              if (feedback) {
                if (isCorrect) stateClass = "correct";
                else if (isSelected) stateClass = "wrong";
              } else if (isSelected) {
                stateClass = "selected";
              }

              return (
                <div
                  key={opt.id}
                  className={`opt${stateClass ? ` ${stateClass}` : ""}`}
                  role="button"
                  tabIndex={feedback ? -1 : 0}
                  onClick={() => {
                    if (feedback || submitting) return;
                    if (currentQuestion.selection_mode === "multiple") {
                      setMultipleSelected((prev) =>
                        prev.includes(opt.id)
                          ? prev.filter((id) => id !== opt.id)
                          : [...prev, opt.id],
                      );
                      return;
                    }
                    void handleSingleSelect(opt.id);
                  }}
                  onKeyDown={(e) => {
                    if (e.key !== "Enter" && e.key !== " ") return;
                    e.preventDefault();
                    if (currentQuestion.selection_mode === "multiple") {
                      setMultipleSelected((prev) =>
                        prev.includes(opt.id)
                          ? prev.filter((id) => id !== opt.id)
                          : [...prev, opt.id],
                      );
                    } else {
                      void handleSingleSelect(opt.id);
                    }
                  }}
                >
                  <span className="om">{letter}</span>
                  <span>{opt.option_text}</span>
                </div>
              );
            })}
          </div>

          {currentQuestion.selection_mode === "multiple" && !feedback ? (
            <button
              type="button"
              className="btn-next"
              disabled={multipleSelected.length === 0 || submitting}
              onClick={() => void handleMultipleSubmit()}
            >
              Ответить
            </button>
          ) : null}

          {feedback?.explanation ? (
            <div className="q-expl show">
              <strong>Разбор:</strong> {feedback.explanation}
            </div>
          ) : null}

          {feedback ? (
            <div className="kb-quiz-next-row">
              <button type="button" className="btn-next" onClick={() => void handleNext()}>
                {questionIndex + 1 >= totalQuestions ? "Показать результат" : "Далее"}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
