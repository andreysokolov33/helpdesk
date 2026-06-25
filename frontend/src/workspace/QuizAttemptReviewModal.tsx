import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  finishKbQuizAttempt,
  submitKbQuizAnswer,
  type KbQuizFinishResult,
  type KbQuizQuestion,
} from "@/api/kb";
import {
  fetchOperatorQuizAttemptReview,
  startOperatorQuizPractice,
  type OperatorQuizAnsweredReview,
  type OperatorQuizAttemptReview,
} from "@/api/operatorQuizReview";
import { dailyQuizScoreStyle } from "@/workspace/dailyQuizScore";
import {
  isAlreadyAnsweredError,
  type QuizAnswerFeedback,
} from "@/workspace/quizFlow";

type Props = {
  attemptId: number | null;
  onClose: () => void;
};

type Mode = "review" | "practice" | "practice-done";

function formatReviewDate(review: OperatorQuizAttemptReview): string {
  const raw = review.session_date ?? review.finished_at;
  if (!raw) return "";
  try {
    const iso = review.session_date ? `${review.session_date}T12:00:00` : raw;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

function feedbackFromReviewEntry(entry: OperatorQuizAnsweredReview): QuizAnswerFeedback {
  return {
    is_correct: entry.is_correct,
    explanation: entry.explanation,
    correct_option_ids: entry.correct_option_ids,
    selectedOptionIds: [...entry.selected_option_ids],
  };
}

export default function QuizAttemptReviewModal({ attemptId, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [review, setReview] = useState<OperatorQuizAttemptReview | null>(null);
  const [mode, setMode] = useState<Mode>("review");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [practiceAttemptId, setPracticeAttemptId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<QuizAnswerFeedback | null>(null);
  const [multipleSelected, setMultipleSelected] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [startingPractice, setStartingPractice] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [practiceResult, setPracticeResult] = useState<KbQuizFinishResult | null>(null);
  const [practiceAnswered, setPracticeAnswered] = useState<OperatorQuizAnsweredReview[]>([]);

  const resetState = useCallback(() => {
    setReview(null);
    setMode("review");
    setQuestionIndex(0);
    setPracticeAttemptId(null);
    setFeedback(null);
    setMultipleSelected([]);
    setPracticeResult(null);
    setPracticeAnswered([]);
    setError("");
  }, []);

  useEffect(() => {
    if (!attemptId) {
      resetState();
      return;
    }
    let cancelled = false;
    resetState();
    setLoading(true);
    fetchOperatorQuizAttemptReview(attemptId)
      .then((data) => {
        if (cancelled) return;
        setReview(data);
        setQuestionIndex(0);
        const first = data.answered.find(
          (a) => Number(a.question_id) === Number(data.questions[0]?.id),
        );
        setFeedback(first ? feedbackFromReviewEntry(first) : null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка загрузки");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [attemptId, resetState]);

  const totalQuestions = review?.questions.length ?? 0;
  const currentQuestion: KbQuizQuestion | null =
    review && questionIndex < totalQuestions ? review.questions[questionIndex] : null;

  const isDaily = review?.attempt_type === "daily_warmup";
  const title =
    review?.article_title ?? (isDaily ? "Ежедневный тест" : "Тест по статье");
  const dateLabel = review ? formatReviewDate(review) : "";

  const progressPct = useMemo(() => {
    if (!totalQuestions) return 0;
    if (mode === "practice-done") return 100;
    return Math.round(((questionIndex + (feedback ? 1 : 0)) / totalQuestions) * 100);
  }, [feedback, mode, questionIndex, totalQuestions]);

  const syncReviewFeedback = useCallback(
    (index: number, data: OperatorQuizAttemptReview) => {
      const q = data.questions[index];
      if (!q) {
        setFeedback(null);
        return;
      }
      const entry = data.answered.find((a) => Number(a.question_id) === Number(q.id));
      setFeedback(entry ? feedbackFromReviewEntry(entry) : null);
    },
    [],
  );

  const syncPracticeFeedback = useCallback(
    (index: number, answered: OperatorQuizAnsweredReview[], questions: KbQuizQuestion[]) => {
      const q = questions[index];
      if (!q) {
        setFeedback(null);
        return;
      }
      const entry = answered.find((a) => Number(a.question_id) === Number(q.id));
      setFeedback(entry ? feedbackFromReviewEntry(entry) : null);
    },
    [],
  );

  const handleReviewNav = (nextIndex: number) => {
    if (!review) return;
    setQuestionIndex(nextIndex);
    setMultipleSelected([]);
    syncReviewFeedback(nextIndex, review);
  };

  const handleStartPractice = async () => {
    if (!review || startingPractice) return;
    setStartingPractice(true);
    setError("");
    try {
      const started = await startOperatorQuizPractice(review.attempt_id);
      setPracticeAttemptId(started.attempt_id);
      setMode("practice");
      setQuestionIndex(0);
      setFeedback(null);
      setMultipleSelected([]);
      setPracticeAnswered([]);
      setPracticeResult(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось начать практику");
    } finally {
      setStartingPractice(false);
    }
  };

  const submitPracticeAnswer = async (selectedOptionIds: number[]) => {
    if (!currentQuestion || !practiceAttemptId || feedback || submitting || !review) return;
    setSubmitting(true);
    setError("");
    try {
      const result = await submitKbQuizAnswer(
        practiceAttemptId,
        currentQuestion.id,
        [...selectedOptionIds].sort((a, b) => a - b),
      );
      const entry: OperatorQuizAnsweredReview = {
        question_id: currentQuestion.id,
        selected_option_ids: [...selectedOptionIds],
        is_correct: result.is_correct,
        correct_option_ids: result.correct_option_ids,
        explanation: result.explanation,
      };
      const nextAnswered = [...practiceAnswered, entry];
      setPracticeAnswered(nextAnswered);
      setFeedback({ ...result, selectedOptionIds });
      setMultipleSelected([]);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Не удалось отправить ответ";
      if (isAlreadyAnsweredError(message)) {
        setError("Ответ уже был сохранён — перейдите к следующему вопросу.");
      } else {
        setError(message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handlePracticeNext = async () => {
    if (!review || !practiceAttemptId || finishing) return;
    const isLast = questionIndex + 1 >= totalQuestions;
    if (isLast) {
      setFinishing(true);
      setError("");
      try {
        const result = await finishKbQuizAttempt(practiceAttemptId);
        setPracticeResult(result);
        setMode("practice-done");
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Не удалось завершить практику");
      } finally {
        setFinishing(false);
      }
      return;
    }
    const nextIndex = questionIndex + 1;
    setQuestionIndex(nextIndex);
    setMultipleSelected([]);
    syncPracticeFeedback(nextIndex, practiceAnswered, review.questions);
  };

  if (!attemptId) return null;

  return (
    <div className="op-quiz-review-overlay" role="dialog" aria-modal="true" aria-labelledby="op-quiz-review-title">
      <div className="op-quiz-review-modal">
        <header className="op-quiz-review-head">
          <div className="op-quiz-review-head-main">
            <span className="op-quiz-review-badge">
              {mode === "practice" || mode === "practice-done" ? "Практика" : "Просмотр"}
            </span>
            <h2 id="op-quiz-review-title" className="op-quiz-review-title">
              {title}
            </h2>
            {dateLabel ? <p className="op-quiz-review-sub">{dateLabel}</p> : null}
            {review?.category_title && !isDaily ? (
              <p className="op-quiz-review-sub">{review.category_title}</p>
            ) : null}
          </div>
          <button type="button" className="op-quiz-review-close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </header>

        {loading ? (
          <div className="op-quiz-review-body op-quiz-muted">Загрузка…</div>
        ) : error && !review ? (
          <div className="op-quiz-review-body">
            <div className="op-error">{error}</div>
          </div>
        ) : review ? (
          <>
            <div className="op-quiz-review-summary">
              <span
                className="op-quiz-score-badge"
                style={dailyQuizScoreStyle(review.correct_count, review.total_questions)}
                title={`${review.score_percent}%`}
              >
                {review.correct_count}/{review.total_questions}
              </span>
              <span className={`op-quiz-pass-tag${review.passed ? " is-pass" : " is-fail"}`}>
                {review.passed ? "Сдан" : "Не сдан"}
              </span>
              {mode === "review" ? (
                <button
                  type="button"
                  className="op-quiz-review-practice-btn"
                  disabled={startingPractice}
                  onClick={() => void handleStartPractice()}
                >
                  {startingPractice ? "Запуск…" : "Пройти для практики"}
                </button>
              ) : (
                <span className="op-quiz-review-practice-note">
                  Результат практики не влияет на статистику
                </span>
              )}
              {review.article_slug ? (
                <Link to={`/kb/${review.article_slug}`} className="op-quiz-review-article-link">
                  К статье →
                </Link>
              ) : null}
            </div>

            {mode === "practice-done" && practiceResult ? (
              <div className="op-quiz-review-body">
                <div className={`quiz-score-box show`}>
                  <div className={`qs-num${practiceResult.passed ? "" : " qs-num--fail"}`}>
                    {practiceResult.passed ? "Практика: сдано" : "Практика: есть ошибки"}
                  </div>
                  <p className="kb-quiz-score-summary">
                    Верно: <strong>{practiceResult.correct_count}</strong> из{" "}
                    <strong>{practiceResult.total_questions}</strong>
                  </p>
                  <p className="op-quiz-review-practice-note">
                    Официальный результат ({review.correct_count}/{review.total_questions}) не изменён.
                  </p>
                  <div className="kb-quiz-score-actions">
                    <button type="button" className="kb-quiz-btn-secondary" onClick={onClose}>
                      Закрыть
                    </button>
                    <button
                      type="button"
                      className="btn-next"
                      onClick={() => {
                        setMode("review");
                        setQuestionIndex(0);
                        setPracticeResult(null);
                        setPracticeAttemptId(null);
                        syncReviewFeedback(0, review);
                      }}
                    >
                      К просмотру ответов
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="op-quiz-review-body">
                <div className="quiz-progress-text">
                  {mode === "practice"
                    ? `Практика · вопрос ${questionIndex + 1} из ${totalQuestions}`
                    : `Вопрос ${questionIndex + 1} из ${totalQuestions} · ваши ответы`}
                </div>
                <div className="quiz-progress-wrap" aria-hidden>
                  <div className="quiz-progress-bar" style={{ width: `${progressPct}%` }} />
                </div>
                {error ? <div className="kb-quiz-inline-error">{error}</div> : null}

                {currentQuestion ? (
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
                            role={mode === "practice" && !feedback ? "button" : undefined}
                            tabIndex={mode === "practice" && !feedback ? 0 : -1}
                            onClick={() => {
                              if (mode !== "practice" || feedback || submitting) return;
                              if (currentQuestion.selection_mode === "multiple") {
                                setMultipleSelected((prev) =>
                                  prev.includes(opt.id)
                                    ? prev.filter((id) => id !== opt.id)
                                    : [...prev, opt.id],
                                );
                                return;
                              }
                              void submitPracticeAnswer([opt.id]);
                            }}
                            onKeyDown={(e) => {
                              if (mode !== "practice" || feedback) return;
                              if (e.key !== "Enter" && e.key !== " ") return;
                              e.preventDefault();
                              if (currentQuestion.selection_mode === "multiple") {
                                setMultipleSelected((prev) =>
                                  prev.includes(opt.id)
                                    ? prev.filter((id) => id !== opt.id)
                                    : [...prev, opt.id],
                                );
                              } else {
                                void submitPracticeAnswer([opt.id]);
                              }
                            }}
                          >
                            <span className="om">{letter}</span>
                            <span>{opt.option_text}</span>
                          </div>
                        );
                      })}
                    </div>

                    {mode === "practice" &&
                    currentQuestion.selection_mode === "multiple" &&
                    !feedback ? (
                      <button
                        type="button"
                        className="btn-next"
                        disabled={multipleSelected.length === 0 || submitting}
                        onClick={() => void submitPracticeAnswer(multipleSelected)}
                      >
                        Ответить
                      </button>
                    ) : null}

                    {feedback?.explanation ? (
                      <div className="q-expl show">
                        <strong>Разбор:</strong> {feedback.explanation}
                      </div>
                    ) : null}

                    {mode === "review" ? (
                      <div className="op-quiz-review-nav">
                        <button
                          type="button"
                          className="kb-quiz-btn-secondary"
                          disabled={questionIndex <= 0}
                          onClick={() => handleReviewNav(questionIndex - 1)}
                        >
                          Назад
                        </button>
                        <button
                          type="button"
                          className="btn-next"
                          disabled={questionIndex + 1 >= totalQuestions}
                          onClick={() => handleReviewNav(questionIndex + 1)}
                        >
                          Далее
                        </button>
                      </div>
                    ) : feedback ? (
                      <div className="kb-quiz-next-row">
                        <button
                          type="button"
                          className="btn-next"
                          disabled={finishing}
                          onClick={() => void handlePracticeNext()}
                        >
                          {questionIndex + 1 >= totalQuestions ? "Завершить практику" : "Далее"}
                        </button>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
