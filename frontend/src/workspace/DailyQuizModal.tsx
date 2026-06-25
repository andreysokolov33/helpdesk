import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchDailyQuizSession,
  finishDailyQuizAttempt,
  startDailyQuizAttempt,
  submitDailyQuizAnswer,
  type DailyQuizHistoryItem,
  type DailyQuizSession,
  type DailyQuizStatus,
} from "@/api/dailyQuiz";
import type { KbQuizFinishResult, KbQuizQuestion } from "@/api/kb";
import {
  dailyQuizScoreStyle,
  formatDailyQuizScoreTitle,
} from "@/workspace/dailyQuizScore";
import {
  feedbackFromAnswered,
  firstUnansweredIndex,
  isAlreadyAnsweredError,
  type QuizAnswerFeedback,
} from "@/workspace/quizFlow";

type Props = {
  status: DailyQuizStatus;
  onComplete: () => void;
};

function formatHistoryTitle(item: DailyQuizHistoryItem): string {
  return formatDailyQuizScoreTitle(item.session_date, item, undefined);
}

function applySessionProgress(
  data: DailyQuizSession,
  setters: {
    setSession: (v: DailyQuizSession) => void;
    setAttemptId: (v: number | null) => void;
    setQuestionIndex: (v: number) => void;
    setFeedback: (v: QuizAnswerFeedback | null) => void;
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

export default function DailyQuizModal({ status, onComplete }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<DailyQuizSession | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(status.attempt_id);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [feedback, setFeedback] = useState<QuizAnswerFeedback | null>(null);
  const [multipleSelected, setMultipleSelected] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [finishResult, setFinishResult] = useState<KbQuizFinishResult | null>(null);
  const [closing, setClosing] = useState(false);
  const [history, setHistory] = useState<DailyQuizHistoryItem[]>(status.history);
  const finishingRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  const statusRef = useRef(status);
  const bootstrapStartedRef = useRef(false);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const dismissModal = useCallback(() => {
    setClosing(true);
    window.setTimeout(() => onCompleteRef.current(), 420);
  }, []);

  const finishAndClose = useCallback(
    async (id: number) => {
      if (finishingRef.current) return;
      finishingRef.current = true;
      try {
        const result = await finishDailyQuizAttempt(id);
        setFinishResult(result);
        const todayPassed = result.passed;
        const sessionDate = statusRef.current.session_date;
        const todayLabel = sessionDate?.slice(8, 10) ?? "";
        if (sessionDate && todayLabel) {
          setHistory((prev) => {
            const filtered = prev.filter((h) => h.session_date !== sessionDate);
            return [
              {
                session_date: sessionDate,
                day_label: todayLabel.replace(/^0/, "") || todayLabel,
                passed: todayPassed,
                status: "finished",
                correct_count: result.correct_count,
                total_questions: result.total_questions,
              },
              ...filtered,
            ]
              .sort((a, b) => b.session_date.localeCompare(a.session_date))
              .slice(0, 7);
          });
        }
      } finally {
        finishingRef.current = false;
      }
    },
    [],
  );

  const finishAndCloseRef = useRef(finishAndClose);
  useEffect(() => {
    finishAndCloseRef.current = finishAndClose;
  }, [finishAndClose]);

  const syncFromSession = useCallback(
    (data: DailyQuizSession) =>
      applySessionProgress(data, {
        setSession,
        setAttemptId,
        setQuestionIndex,
        setFeedback,
        setMultipleSelected,
      }),
    [],
  );

  const loadQuiz = useCallback(async (retry = false) => {
    if (bootstrapStartedRef.current && !retry) return;
    bootstrapStartedRef.current = true;

    setLoading(true);
    if (retry) {
      setError(null);
      setFeedback(null);
      setMultipleSelected([]);
      setFinishResult(null);
    }
    try {
      let data = await fetchDailyQuizSession();
      if (data.attempt_status === "finished" && data.attempt_id) {
        setSession(data);
        setAttemptId(data.attempt_id);
        setQuestionIndex(data.questions.length);
        setLoading(false);
        onCompleteRef.current();
        return;
      }
      if (data.attempt_status !== "in_progress" || !data.attempt_id) {
        const started = await startDailyQuizAttempt();
        setAttemptId(started.attempt_id);
        data = await fetchDailyQuizSession();
      }
      const idx = syncFromSession(data);
      if (idx >= data.questions.length && data.attempt_id) {
        await finishAndCloseRef.current(data.attempt_id);
      }
    } catch (e) {
      bootstrapStartedRef.current = false;
      setError(e instanceof Error ? e.message : "Не удалось загрузить тест");
    } finally {
      setLoading(false);
    }
  }, [syncFromSession]);

  useEffect(() => {
    void loadQuiz();
  }, [loadQuiz]);

  const totalQuestions = session?.questions.length ?? 0;
  const currentQuestion: KbQuizQuestion | null =
    session && questionIndex < totalQuestions ? session.questions[questionIndex] : null;

  const progressPct = useMemo(() => {
    if (!totalQuestions) return 0;
    if (finishResult) return 100;
    const answeredCount = feedback ? questionIndex + 1 : questionIndex;
    return Math.round((answeredCount / totalQuestions) * 100);
  }, [feedback, finishResult, questionIndex, totalQuestions]);

  const passed = finishResult?.passed ?? false;
  const correctCount = finishResult?.correct_count ?? 0;
  const errorCount = finishResult?.error_count ?? 0;

  const submitAnswer = async (selectedOptionIds: number[]) => {
    if (!currentQuestion || !attemptId || feedback || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await submitDailyQuizAnswer(
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
          const fresh = await fetchDailyQuizSession();
          const idx = syncFromSession(fresh);
          if (idx >= fresh.questions.length && fresh.attempt_id) {
            await finishAndClose(fresh.attempt_id);
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

  const handleOptionClick = (optionId: number) => {
    if (!currentQuestion || feedback || submitting) return;
    if (currentQuestion.selection_mode === "multiple") {
      setMultipleSelected((prev) =>
        prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId],
      );
      return;
    }
    void submitAnswer([optionId]);
  };

  const handleNext = async () => {
    if (!session || !attemptId || finishingRef.current) return;
    if (questionIndex + 1 >= totalQuestions) {
      try {
        await finishAndClose(attemptId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Не удалось завершить тест");
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

  const recentHistory = useMemo(
    () =>
      [...history]
        .sort((a, b) => b.session_date.localeCompare(a.session_date))
        .slice(0, 7),
    [history],
  );

  return (
    <div className={`daily-quiz-overlay${closing ? " daily-quiz-overlay--out" : ""}`} role="dialog" aria-modal="true">
      <div className={`daily-quiz-modal${closing ? " daily-quiz-modal--out" : ""}`}>
        <aside className="daily-quiz-modal__aside">
          <div className="daily-quiz-modal__aside-title">Последние тесты</div>
          <div className="daily-quiz-history" aria-label="История ежедневных тестов">
            {recentHistory.length === 0 ? (
              <div className="daily-quiz-history__empty">Пока нет завершённых тестов</div>
            ) : (
              <div className="daily-quiz-history__track">
                {recentHistory.map((item, index) => (
                  <div key={item.session_date} className="daily-quiz-history__node">
                    <span
                      className="daily-quiz-history__dot"
                      style={dailyQuizScoreStyle(item.correct_count, item.total_questions)}
                      title={formatHistoryTitle(item)}
                    >
                      {item.day_label}
                    </span>
                    {index < recentHistory.length - 1 ? (
                      <span className="daily-quiz-history__stem" aria-hidden />
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        <div className="daily-quiz-modal__main">
          <header className="daily-quiz-modal__head">
            <span className="daily-quiz-modal__badge">Ежедневный тест</span>
            <h2 className="daily-quiz-modal__title">{status.title ?? "Проверка знаний"}</h2>
            <p className="daily-quiz-modal__sub">
              {status.questions_per_session ?? totalQuestions} вопросов на сегодня. Одна попытка в сутки.
            </p>
          </header>

          {loading ? (
            <div className="daily-quiz-loading">Подготовка теста…</div>
          ) : error && !session ? (
            <div className="daily-quiz-error">
              <p>{error}</p>
              <button type="button" className="daily-quiz-btn" onClick={() => void loadQuiz(true)}>
                Повторить
              </button>
            </div>
          ) : finishResult ? (
            <div className={`daily-quiz-result${passed ? " daily-quiz-result--pass" : " daily-quiz-result--fail"}`}>
              {passed ? (
                <div className="daily-quiz-celebrate" aria-hidden>
                  <span className="daily-quiz-celebrate__ring" />
                  <span className="daily-quiz-celebrate__icon">✓</span>
                </div>
              ) : (
                <div className="daily-quiz-result__icon daily-quiz-result__icon--fail">!</div>
              )}
              <div className="daily-quiz-result__title">
                {passed ? "Отлично!" : "Есть ошибки"}
              </div>
              <p className="daily-quiz-result__score">
                Верно: <strong>{correctCount}</strong> из <strong>{totalQuestions}</strong>
                {errorCount > 0 ? (
                  <>
                    {" "}
                    · ошибок: <strong>{errorCount}</strong>
                  </>
                ) : null}
              </p>
              <p className="daily-quiz-result__hint">
                {passed
                  ? "Хороший старт смены. Можно приступать к работе."
                  : "Рекомендуем повторить материалы в базе знаний — это поможет в работе с абонентами."}
              </p>
              <div className="daily-quiz-result__actions">
                {!passed ? (
                  <Link to="/kb" className="daily-quiz-kb-link" onClick={dismissModal}>
                    Перейти в базу знаний →
                  </Link>
                ) : null}
                <button type="button" className="daily-quiz-btn daily-quiz-btn--primary" onClick={dismissModal}>
                  Продолжить работу
                </button>
              </div>
            </div>
          ) : currentQuestion ? (
            <>
              <div className="daily-quiz-progress-meta">
                Вопрос {questionIndex + 1} из {totalQuestions}
                {currentQuestion.selection_mode === "multiple" && !feedback ? (
                  <span className="daily-quiz-multiple-hint"> · можно выбрать несколько вариантов</span>
                ) : null}
              </div>
              <div className="daily-quiz-progress" aria-hidden>
                <div className="daily-quiz-progress__bar" style={{ width: `${progressPct}%` }} />
              </div>
              {error ? <div className="daily-quiz-inline-error">{error}</div> : null}
              <div className={`daily-quiz-qblock${feedback ? " is-answered" : ""}`}>
                <div className="daily-quiz-qtext">{currentQuestion.question_text}</div>
                <div className="daily-quiz-opts">
                  {currentQuestion.options.map((opt, optIdx) => {
                    const letter = String.fromCharCode(65 + optIdx);
                    const isSelected = feedback
                      ? feedback.selectedOptionIds.includes(opt.id)
                      : multipleSelected.includes(opt.id);
                    const isCorrect = feedback?.correct_option_ids.includes(opt.id);
                    let stateClass = "";
                    if (feedback) {
                      if (isCorrect) stateClass = "is-correct";
                      else if (isSelected) stateClass = "is-wrong";
                    } else if (isSelected) {
                      stateClass = "is-selected";
                    }
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        className={`daily-quiz-opt${stateClass ? ` ${stateClass}` : ""}`}
                        disabled={Boolean(feedback) || submitting}
                        onClick={() => handleOptionClick(opt.id)}
                      >
                        <span className="daily-quiz-opt__letter">{letter}</span>
                        <span>{opt.option_text}</span>
                      </button>
                    );
                  })}
                </div>

                {currentQuestion.selection_mode === "multiple" && !feedback ? (
                  <div className="daily-quiz-next-row">
                    <button
                      type="button"
                      className="daily-quiz-btn daily-quiz-btn--primary"
                      disabled={multipleSelected.length === 0 || submitting}
                      onClick={() => void submitAnswer(multipleSelected)}
                    >
                      Ответить
                    </button>
                  </div>
                ) : null}

                {feedback?.explanation ? (
                  <div className="daily-quiz-expl">
                    <strong>Разбор:</strong> {feedback.explanation}
                  </div>
                ) : null}
                {feedback ? (
                  <div className="daily-quiz-next-row">
                    <button type="button" className="daily-quiz-btn daily-quiz-btn--primary" onClick={() => void handleNext()}>
                      {questionIndex + 1 >= totalQuestions ? "Завершить" : "Далее"}
                    </button>
                  </div>
                ) : null}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
