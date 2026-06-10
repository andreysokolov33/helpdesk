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

type SummaryRow = { label: string; value: string };

function formatConnectionTypes(inner: string): string {
  return inner
    .split(",")
    .map((part) => part.replace(/:\s*\d+\s*$/, "").trim())
    .filter(Boolean)
    .join(", ");
}

function buildFastCheckSummary(steps: FastCheckStep[]): SummaryRow[] {
  const byCode = new Map(steps.map((s) => [s.test_code, s]));
  const rows: SummaryRow[] = [];

  const push = (code: string, label: string) => {
    const step = byCode.get(code);
    if (!step) return;
    if (step.status === "skip" && !step.detail?.trim()) return;
    const value =
      step.detail?.trim() ||
      (step.status === "pass" ? "В порядке" : step.status === "skip" ? "Не проверялось" : "—");
    rows.push({ label, value });
  };

  push("account_status", "Статус УЗ");
  push("tariff_state", "Наличие тарифа");
  push("balance_tariff", "Баланс");
  push("station_aliveness", "Станция на связи");

  const sessions = byCode.get("active_sessions");
  if (sessions) {
    const detail = sessions.detail ?? "";
    const parenOpen = detail.indexOf("(");
    const parenClose = detail.lastIndexOf(")");
    if (parenOpen !== -1 && parenClose > parenOpen) {
      const conn = formatConnectionTypes(detail.slice(parenOpen + 1, parenClose));
      if (conn) rows.push({ label: "Тип соединения", value: conn });
    }
    const countM = detail.match(/Активных сессий:\s*(\d+)/i);
    rows.push({
      label: "Наличие сессий",
      value: countM ? `${countM[1]} активных` : detail.split("(")[0].trim() || "Есть",
    });
  }

  push("session_limit", "Лимит сессий");
  return rows;
}

type Props = {
  userId: number;
  onDisconnect?: () => void;
  onUnarchive?: () => void;
  /** split — как в профиле; stacked — шаги сверху, решение снизу (тикет). */
  layout?: "split" | "stacked";
  /** Скрыть intro и кнопку запуска (запуск снаружи). */
  hideIdleUI?: boolean;
  introText?: string;
  runButtonLabel?: string;
  /** Кэш результата при повторном открытии панели. */
  initialData?: FastCheckResponse | null;
  onResult?: (data: FastCheckResponse) => void;
  /** Запустить проверку при монтировании, если нет initialData. */
  autoRun?: boolean;
  repeatLabel?: string;
  onPhaseChange?: (phase: "idle" | "loading" | "reveal" | "done") => void;
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

function applyResultState(
  res: FastCheckResponse,
  setters: {
    setData: (d: FastCheckResponse) => void;
    setSelectedIdx: (i: number) => void;
    setVisibleCount: (n: number) => void;
    setPhase: (p: "idle" | "loading" | "reveal" | "done") => void;
  },
  phase: "reveal" | "done",
) {
  setters.setData(res);
  const failIdx = res.steps.findIndex((s) => s.status === "fail" || s.status === "warn");
  setters.setSelectedIdx(failIdx >= 0 ? failIdx : Math.max(0, res.steps.length - 1));
  if (phase === "done") {
    setters.setVisibleCount(res.steps.length);
  }
  setters.setPhase(phase);
}

export default function FastCheckPanel({
  userId,
  onDisconnect,
  onUnarchive,
  layout = "split",
  hideIdleUI = false,
  introText = INTRO,
  runButtonLabel = "Проверить абонента",
  initialData = null,
  onResult,
  autoRun = false,
  repeatLabel = "Повторить проверку",
  onPhaseChange,
}: Props) {
  const [phase, setPhase] = useState<"idle" | "loading" | "reveal" | "done">("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<FastCheckResponse | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const revealRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoRunDoneRef = useRef(false);

  const setPhaseTracked = useCallback(
    (p: "idle" | "loading" | "reveal" | "done") => {
      setPhase(p);
      onPhaseChange?.(p);
    },
    [onPhaseChange],
  );

  const clearReveal = useCallback(() => {
    if (revealRef.current) {
      clearInterval(revealRef.current);
      revealRef.current = null;
    }
  }, []);

  useEffect(() => () => clearReveal(), [clearReveal]);

  const runCheck = useCallback(async () => {
    setError(null);
    setData(null);
    setVisibleCount(0);
    clearReveal();
    setPhaseTracked("loading");
    try {
      const res = await postFastCheck(userId);
      onResult?.(res);
      applyResultState(
        res,
        { setData, setSelectedIdx, setVisibleCount, setPhase: setPhaseTracked },
        "reveal",
      );
    } catch (e: unknown) {
      setPhaseTracked("idle");
      setError(e instanceof Error ? e.message : "Ошибка проверки");
    }
  }, [userId, onResult, clearReveal, setPhaseTracked]);

  useEffect(() => {
    if (!initialData?.steps.length) return;
    applyResultState(
      initialData,
      { setData, setSelectedIdx, setVisibleCount, setPhase: setPhaseTracked },
      "done",
    );
  }, [initialData, setPhaseTracked]);

  useEffect(() => {
    if (!autoRun || autoRunDoneRef.current || initialData?.steps.length) return;
    autoRunDoneRef.current = true;
    void runCheck();
  }, [autoRun, initialData, runCheck]);

  useEffect(() => {
    if (phase !== "reveal" || !data?.steps.length) return;
    setVisibleCount(1);
    let n = 1;
    revealRef.current = setInterval(() => {
      n += 1;
      if (n > data.steps.length) {
        clearReveal();
        setPhaseTracked("done");
        setVisibleCount(data.steps.length);
        return;
      }
      setVisibleCount(n);
    }, REVEAL_MS);
    return clearReveal;
  }, [phase, data, clearReveal, setPhaseTracked]);

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

  const showPanel = phase !== "idle" || data !== null;

  const showIdle = phase === "idle" && !data && !hideIdleUI;

  const noProblemsFound = Boolean(
    data?.steps.length &&
      !data.steps.some((s) => s.status === "fail" || s.status === "warn"),
  );

  const panelScroll = Boolean(showPanel && data && phase !== "loading");

  const gridClass = layout === "stacked" ? "up-fc-grid up-fc-grid--stacked" : "up-fc-grid";

  return (
    <div
      className={`up-fast-check${panelScroll ? " up-fast-check--panel-scroll" : " up-fast-check--page-scroll"}`}
    >
      {showIdle ? <p className="up-fc-intro">{introText}</p> : null}

      {showIdle ? (
        <button type="button" className="up-fc-run-btn" onClick={() => void runCheck()}>
          {runButtonLabel}
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
        <div className={gridClass}>
          <div className="up-fc-actions">
            {phase === "done" && noProblemsFound ? (
              <div className="up-fc-success-panel">
                <div className="up-fc-no-problems" role="status">
                  Проблем не обнаружено
                </div>
                <ul className="up-fc-summary" aria-label="Краткие результаты проверки">
                  {buildFastCheckSummary(data.steps).map((row) => (
                    <li key={row.label} className="up-fc-summary-row">
                      <span className="up-fc-summary-k">{row.label}</span>
                      <span className="up-fc-summary-v">{row.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : showActions ? (
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
            {activeStep?.test_code === "account_status" &&
            activeStep.status === "fail" &&
            onUnarchive ? (
              <button type="button" className="up-btn up-btn-restore up-fc-unarchive" onClick={onUnarchive}>
                Восстановить УЗ
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
          <button type="button" className="up-btn sec" onClick={() => void runCheck()}>
            {repeatLabel}
          </button>
          {noProblemsFound ? null : data.stopped_at ? (
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
