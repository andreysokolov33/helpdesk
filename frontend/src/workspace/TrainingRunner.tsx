import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchTrainingNextQuestion,
  fetchTrainingSession,
  finishTrainingSession,
  submitTrainingAnswer,
  trainingArticleHref,
  type TrainingAnswerResult,
  type TrainingNextQuestion,
  type TrainingSessionState,
} from "@/api/training";
import { quizScoreClass } from "@/api/statsQuizTraining";
import { formatClock, secondsSince } from "@/workspace/trainingFormat";

type Props = {
  session: TrainingSessionState;
  onEnded: (session: TrainingSessionState, notice?: string, completed?: boolean) => void;
  /** false — вкладка скрыта: горячие клавиши не перехватываем. */
  active?: boolean;
};

type Feedback = TrainingAnswerResult & { selectedOptionIds: number[] };

function isSessionClosedError(message: string): boolean {
  return /завершена/i.test(message);
}

function isStaleQuestionError(message: string): boolean {
  return /не актуален/i.test(message);
}

export default function TrainingRunner({ session: initialSession, onEnded, active = true }: Props) {
  const [session, setSession] = useState<TrainingSessionState>(initialSession);
  const [next, setNext] = useState<TrainingNextQuestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const nextBtnRef = useRef<HTMLButtonElement>(null);
  const sessionId = initialSession.id;

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const endWithServerState = useCallback(
    async (notice?: string) => {
      try {
        const fresh = await fetchTrainingSession(sessionId);
        onEnded(fresh, notice);
      } catch {
        onEnded(session, notice);
      }
    },
    [onEnded, session, sessionId],
  );

  const loadNext = useCallback(async () => {
    setLoading(true);
    setError(null);
    setFeedback(null);
    setSelected([]);
    try {
      const data = await fetchTrainingNextQuestion(sessionId);
      setSession(data.session);
      if (data.session.status !== "in_progress") {
        onEnded(
          data.session,
          data.session.status === "abandoned"
            ? `Тренировка завершена автоматически: не было ответов более ${data.session.inactivity_minutes} мин.`
            : undefined,
        );
        return;
      }
      if (!data.question) {
        setError("В выбранном источнике сейчас нет вопросов. Завершите тренировку и выберите другой источник.");
      }
      setNext(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить вопрос");
    } finally {
      setLoading(false);
    }
  }, [onEnded, sessionId]);

  useEffect(() => {
    void loadNext();
  }, [loadNext]);

  useEffect(() => {
    if (feedback) nextBtnRef.current?.focus();
  }, [feedback]);

  const question = next?.question ?? null;

  const submit = useCallback(
    async (optionIds: number[]) => {
      if (!question || feedback || submitting || optionIds.length === 0) return;
      setSubmitting(true);
      setError(null);
      try {
        const result = await submitTrainingAnswer(
          sessionId,
          question.id,
          [...optionIds].sort((a, b) => a - b),
        );
        setSession(result.session);
        setFeedback({ ...result, selectedOptionIds: optionIds });
        setSelected([]);
      } catch (e) {
        const message = e instanceof Error ? e.message : "Не удалось отправить ответ";
        if (isSessionClosedError(message)) {
          await endWithServerState(message);
          return;
        }
        if (isStaleQuestionError(message)) {
          await loadNext();
          return;
        }
        setError(message);
      } finally {
        setSubmitting(false);
      }
    },
    [endWithServerState, feedback, loadNext, question, sessionId, submitting],
  );

  const toggleOption = useCallback(
    (optionId: number) => {
      if (!question || feedback || submitting) return;
      if (question.selection_mode === "multiple") {
        setSelected((prev) => (prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId]));
        return;
      }
      void submit([optionId]);
    },
    [feedback, question, submit, submitting],
  );

  const finish = useCallback(async () => {
    if (finishing) return;
    setFinishing(true);
    setError(null);
    try {
      const state = await finishTrainingSession(sessionId);
      onEnded(state);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось завершить тренировку");
      setFinishing(false);
    }
  }, [finishing, onEnded, sessionId]);

  // Клавиатура: 1–9 — выбрать вариант, Enter — ответить / следующий вопрос.
  useEffect(() => {
    if (!active) return;
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      if (!question || loading) return;
      if (/^[1-9]$/.test(e.key) && !feedback) {
        const opt = question.options[Number(e.key) - 1];
        if (opt) {
          e.preventDefault();
          toggleOption(opt.id);
        }
        return;
      }
      if (e.key === "Enter" && !feedback && question.selection_mode === "multiple" && selected.length > 0) {
        e.preventDefault();
        void submit(selected);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, feedback, loading, question, selected, submit, toggleOption]);

  const total = session.total_answers;
  const correct = session.correct_count;
  const wrong = session.wrong_count;
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : null;
  const elapsed = secondsSince(session.started_at, nowMs);
  const poolSize = next?.pool_size ?? 0;
  const roundPos = next?.round_position ?? 0;
  const roundPct = poolSize > 0 ? Math.round(((feedback ? roundPos : roundPos - 1) / poolSize) * 100) : 0;

  return (
    <div className="trn-run">
      <header className="trn-hud">
        <div className="trn-hud__source">
          <span className="trn-hud__kind">{session.source_kind_label}</span>
          <span className="trn-hud__title" title={session.source_title}>
            {session.source_title}
          </span>
        </div>
        <dl className="trn-hud__stats">
          <div className="trn-stat trn-stat--good">
            <dt>Верно</dt>
            <dd key={`c-${correct}`} className={feedback?.is_correct ? "trn-bump" : undefined}>
              {correct}
            </dd>
          </div>
          <div className="trn-stat trn-stat--bad">
            <dt>Неверно</dt>
            <dd key={`w-${wrong}`} className={feedback && !feedback.is_correct ? "trn-bump" : undefined}>
              {wrong}
            </dd>
          </div>
          <div className="trn-stat">
            <dt>Точность</dt>
            <dd className={accuracy != null ? quizScoreClass(accuracy) : undefined}>
              {accuracy != null ? `${accuracy}%` : "—"}
            </dd>
          </div>
          <div className="trn-stat" title="Итоговое время считается до последнего ответа">
            <dt>Время</dt>
            <dd className="trn-stat__clock">{formatClock(elapsed)}</dd>
          </div>
        </dl>
        <button
          type="button"
          className="trn-btn trn-btn--finish"
          onClick={() => void finish()}
          disabled={finishing}
        >
          {finishing ? "Завершаем…" : "Завершить"}
        </button>
      </header>

      <div className="trn-progress">
        <div className="trn-progress__text">
          {poolSize > 0 ? (
            <>
              Вопрос {roundPos} из {poolSize}
              {question?.selection_mode === "multiple" && !feedback ? (
                <span className="trn-progress__hint"> · можно выбрать несколько вариантов</span>
              ) : null}
            </>
          ) : (
            "Загрузка вопросов…"
          )}
        </div>
        <div className="quiz-progress-wrap trn-progress__bar" aria-hidden>
          <div className="quiz-progress-bar" style={{ width: `${Math.max(0, roundPct)}%` }} />
        </div>
      </div>

      {error ? (
        <div className="trn-alert" role="alert">
          <span>{error}</span>
          {!question ? (
            <button type="button" className="kb-quiz-btn-secondary" onClick={() => void loadNext()}>
              Повторить
            </button>
          ) : null}
        </div>
      ) : null}

      {loading && !question ? (
        <div className="trn-qcard trn-qcard--loading" aria-busy="true">
          <div className="trn-skeleton trn-skeleton--line" />
          <div className="trn-skeleton trn-skeleton--opt" />
          <div className="trn-skeleton trn-skeleton--opt" />
          <div className="trn-skeleton trn-skeleton--opt" />
        </div>
      ) : question ? (
        <div className={`trn-qcard qblock${feedback ? " answered" : ""}${loading ? " is-loading" : ""}`} key={question.id}>
          <div className="q-text">{question.question_text}</div>
          <div className="q-opts" role={question.selection_mode === "multiple" ? "group" : "radiogroup"}>
            {question.options.map((opt, idx) => {
              const isSelected = feedback ? feedback.selectedOptionIds.includes(opt.id) : selected.includes(opt.id);
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
                  role={question.selection_mode === "multiple" ? "checkbox" : "radio"}
                  aria-checked={isSelected}
                  aria-disabled={Boolean(feedback) || submitting}
                  tabIndex={feedback ? -1 : 0}
                  onClick={() => toggleOption(opt.id)}
                  onKeyDown={(e) => {
                    if (e.key !== "Enter" && e.key !== " ") return;
                    e.preventDefault();
                    e.stopPropagation();
                    toggleOption(opt.id);
                  }}
                >
                  <span className="om">{idx + 1}</span>
                  <span>{opt.option_text}</span>
                </div>
              );
            })}
          </div>

          {question.selection_mode === "multiple" && !feedback ? (
            <div className="trn-actions">
              <button
                type="button"
                className="trn-btn trn-btn--primary"
                disabled={selected.length === 0 || submitting}
                onClick={() => void submit(selected)}
              >
                {submitting ? "Проверяем…" : "Ответить"}
              </button>
            </div>
          ) : null}

          {feedback ? (
            <div className={`trn-feedback trn-feedback--${feedback.is_correct ? "ok" : "fail"}`} aria-live="polite">
              <div className="trn-feedback__verdict">
                <span className="trn-feedback__mark" aria-hidden>
                  {feedback.is_correct ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6">
                      <path d="m5 12.5 4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6">
                      <path d="M7 7l10 10M17 7 7 17" strokeLinecap="round" />
                    </svg>
                  )}
                </span>
                {feedback.is_correct ? "Верно" : "Неверно"}
              </div>
              {feedback.explanation ? <p className="trn-feedback__expl">{feedback.explanation}</p> : null}
              <div className="trn-feedback__actions">
                {!feedback.is_correct && feedback.article ? (
                  <a
                    className="trn-article-link"
                    href={trainingArticleHref(feedback.article.slug)}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={`Откроется в новой вкладке: ${feedback.article.title}`}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" aria-hidden>
                      <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v15H5.5A1.5 1.5 0 0 1 4 17.5v-12ZM20 5.5A1.5 1.5 0 0 0 18.5 4H13v15h5.5a1.5 1.5 0 0 0 1.5-1.5v-12Z" strokeLinejoin="round" />
                    </svg>
                    <span>
                      Прочитать статью
                      <span className="trn-article-link__title">{feedback.article.title}</span>
                    </span>
                  </a>
                ) : (
                  <span />
                )}
                <button
                  type="button"
                  ref={nextBtnRef}
                  className="trn-btn trn-btn--primary"
                  onClick={() => (feedback.completed ? onEnded(feedback.session, undefined, true) : void loadNext())}
                  disabled={loading}
                >
                  {feedback.completed ? "Посмотреть результат" : loading ? "Загрузка…" : "Следующий вопрос"}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <p className="trn-hint">
        Клавиши 1–{Math.min(question?.options.length ?? 4, 9)} выбирают вариант, Enter — следующий вопрос. Тренировка завершится сама, когда
        будут пройдены все вопросы или не будет ответов более {session.inactivity_minutes} мин.
      </p>
    </div>
  );
}
