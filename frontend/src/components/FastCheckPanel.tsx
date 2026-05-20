import { useCallback, useEffect, useRef, useState } from "react";
import {
  postFastCheck,
  type FastCheckResponse,
  type FastCheckStep,
  type ManagerContact,
} from "@/api/userProfile";

const INTRO =
  "Для быстрой проверки состояния УЗ пользователя нажмите кнопку «Проверить абонента». " +
  "Автоматически будет выполнена проверка возможных причин проблем с подключением к сети " +
  "и предложен алгоритм действий.";

const REVEAL_MS = 420;

function stoppedAtLabel(stoppedAt: string, steps: FastCheckStep[]): string {
  const step = steps.find((s) => s.test_code === stoppedAt || s.check_label === stoppedAt);
  return step?.check_label ?? stoppedAt;
}

type Props = {
  userId: number;
  onDisconnect?: () => void;
};

function StatusIcon({ status }: { status: FastCheckStep["status"] | "pending" | "running" }) {
  if (status === "running") return <span className="up-fc-ico up-fc-ico--run" aria-hidden />;
  if (status === "pending") return <span className="up-fc-ico up-fc-ico--pend" aria-hidden>○</span>;
  if (status === "pass") return <span className="up-fc-ico up-fc-ico--ok" aria-hidden>✓</span>;
  if (status === "warn") return <span className="up-fc-ico up-fc-ico--warn" aria-hidden>!</span>;
  if (status === "skip") return <span className="up-fc-ico up-fc-ico--skip" aria-hidden>—</span>;
  return <span className="up-fc-ico up-fc-ico--fail" aria-hidden>✕</span>;
}

function ManagersBlock({ contacts }: { contacts: ManagerContact[] }) {
  if (!contacts.length) return null;
  return (
    <div className="up-fc-managers">
      <div className="up-fc-managers-title">Менеджеры по работе с ЮЛ</div>
      <ul>
        {contacts.map((m, i) => (
          <li key={`${m.full_name ?? ""}-${i}`}>
            {m.full_name ? <strong>{m.full_name}</strong> : null}
            {m.phones.length > 0 ? (
              <div>
                {m.phones.map((ph) => (
                  <span key={ph} className="up-fc-mgr-line">
                    {ph}
                  </span>
                ))}
              </div>
            ) : null}
            {m.emails.length > 0 ? (
              <div className="up-fc-mgr-emails">
                {m.emails.map((em) => (
                  <a key={em} href={`mailto:${em}`}>
                    {em}
                  </a>
                ))}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function FastCheckPanel({ userId, onDisconnect }: Props) {
  const [phase, setPhase] = useState<"idle" | "loading" | "reveal" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<FastCheckResponse | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const revealRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearReveal = useCallback(() => {
    if (revealRef.current) {
      clearInterval(revealRef.current);
      revealRef.current = null;
    }
  }, []);

  useEffect(() => () => clearReveal(), [clearReveal]);

  useEffect(() => {
    if (phase !== "reveal" || !data?.steps.length) return;
    setVisibleCount(1);
    let n = 1;
    revealRef.current = setInterval(() => {
      n += 1;
      if (n > data.steps.length) {
        clearReveal();
        setPhase("done");
        setVisibleCount(data.steps.length);
        return;
      }
      setVisibleCount(n);
    }, REVEAL_MS);
    return clearReveal;
  }, [phase, data, clearReveal]);

  const visibleSteps = data?.steps.slice(0, visibleCount) ?? [];
  const activeIdx =
    phase === "done"
      ? selectedIdx
      : phase === "reveal"
        ? visibleCount - 1
        : visibleCount > 0
          ? visibleCount - 1
          : -1;
  const activeStep = activeIdx >= 0 && data ? data.steps[activeIdx] : null;
  const showActions =
    activeStep &&
    (activeStep.status === "fail" || activeStep.status === "warn") &&
    activeStep.actions_html;

  async function runCheck() {
    setError(null);
    setData(null);
    setVisibleCount(0);
    clearReveal();
    setPhase("loading");
    try {
      const res = await postFastCheck(userId);
      setData(res);
      const failIdx = res.steps.findIndex((s) => s.status === "fail" || s.status === "warn");
      setSelectedIdx(failIdx >= 0 ? failIdx : Math.max(0, res.steps.length - 1));
      setPhase("reveal");
    } catch (e: unknown) {
      setPhase("idle");
      setError(e instanceof Error ? e.message : "Ошибка проверки");
    }
  }

  const showPanel = phase !== "idle" || data !== null;

  const showIdle = phase === "idle" && !data;

  return (
    <div className="up-fast-check">
      {showIdle ? <p className="up-fc-intro">{INTRO}</p> : null}

      {showIdle ? (
        <button type="button" className="up-fc-run-btn" onClick={runCheck}>
          Проверить абонента
        </button>
      ) : null}

      {phase === "loading" ? (
        <div className="up-fc-loading">
          <span className="up-fc-ico up-fc-ico--run" aria-hidden />
          Выполняем проверки…
        </div>
      ) : null}

      {error ? <p className="up-muted up-error">{error}</p> : null}

      {showPanel && data && phase !== "loading" ? (
        <div className="up-fc-grid">
          <div className="up-fc-actions">
            {showActions ? (
              <div
                className="up-fc-html fc-block-wrap"
                dangerouslySetInnerHTML={{ __html: activeStep!.actions_html! }}
              />
            ) : activeStep?.status === "pass" || activeStep?.status === "skip" ? (
              <p className="up-fc-ok-msg">
                {activeStep.detail || "Проверка пройдена. Переходим к следующему шагу…"}
              </p>
            ) : (
              <p className="up-muted">Выберите шаг справа или дождитесь завершения проверки.</p>
            )}
            {data.manager_contacts.length > 0 ? <ManagersBlock contacts={data.manager_contacts} /> : null}
            {activeStep?.test_code === "session_limit" && activeStep.status === "fail" && onDisconnect ? (
              <button type="button" className="up-btn sec up-fc-disconnect" onClick={onDisconnect}>
                Закрыть сессии
              </button>
            ) : null}
          </div>

          <ol className="up-fc-steps" aria-label="Шаги проверки">
            {data.steps.map((step, i) => {
              const revealed = phase === "done" || i < visibleCount;
              const isCurrent =
                phase === "done" ? i === selectedIdx : i === activeIdx && phase === "reveal";
              let displayStatus: FastCheckStep["status"] | "pending" | "running" = "pending";
              if (revealed) displayStatus = step.status;
              else if (isCurrent) displayStatus = "running";
              return (
                <li
                  key={`${step.test_code}-${step.variant}-${i}`}
                  role={phase === "done" ? "button" : undefined}
                  tabIndex={phase === "done" ? 0 : undefined}
                  className={`up-fc-step${revealed ? " revealed" : ""}${isCurrent ? " current" : ""}${phase === "done" && i === selectedIdx ? " selected" : ""}`}
                  onClick={phase === "done" ? () => setSelectedIdx(i) : undefined}
                  onKeyDown={
                    phase === "done"
                      ? (e) => {
                          if (e.key === "Enter" || e.key === " ") setSelectedIdx(i);
                        }
                      : undefined
                  }
                >
                  <StatusIcon status={displayStatus} />
                  <span className="up-fc-step-label">{step.check_label}</span>
                  {revealed && step.detail ? (
                    <span className="up-fc-step-detail">{step.detail}</span>
                  ) : null}
                </li>
              );
            })}
            {phase === "reveal" && visibleCount < (data?.steps.length ?? 0) ? (
              <li className="up-fc-step current">
                <StatusIcon status="running" />
                <span className="up-fc-step-label">Следующая проверка…</span>
              </li>
            ) : null}
          </ol>
        </div>
      ) : null}

      {phase === "done" && data ? (
        <div className="up-fc-done-bar">
          <button type="button" className="up-btn sec" onClick={runCheck}>
            Повторить проверку
          </button>
          {data.stopped_at ? (
            <span className="up-muted">
              Остановлено на: {stoppedAtLabel(data.stopped_at, data.steps)}
            </span>
          ) : (
            <span className="up-fc-all-ok">Все проверки пройдены</span>
          )}
        </div>
      ) : null}
    </div>
  );
}
