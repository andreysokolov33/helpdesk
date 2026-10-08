import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchAuthMe } from "@/api/auth";
import {
  fetchActiveTrainingSession,
  fetchTrainingSources,
  startTrainingSession,
  type TrainingSessionState,
  type TrainingSources,
} from "@/api/training";
import TrainingAdminPanel from "@/workspace/TrainingAdminPanel";
import TrainingHistory from "@/workspace/TrainingHistory";
import TrainingRunner from "@/workspace/TrainingRunner";
import TrainingSourcePicker, { type TrainingStartChoice } from "@/workspace/TrainingSourcePicker";
import TrainingSummary from "@/workspace/TrainingSummary";

type Pane = "train" | "history" | "team";

type TrainView =
  | { kind: "picker" }
  | { kind: "running"; session: TrainingSessionState }
  | { kind: "summary"; session: TrainingSessionState; notice?: string; completed?: boolean };

function parsePane(raw: string | null, isAdmin: boolean): Pane {
  if (raw === "history") return "history";
  if (raw === "team" && isAdmin) return "team";
  return "train";
}

function choiceFromSession(s: TrainingSessionState): TrainingStartChoice {
  if (s.source_type === "daily") return { source_type: "daily" };
  if (s.article_id != null) return { source_type: "article", article_id: s.article_id };
  if (s.category_id != null) return { source_type: "article", category_id: s.category_id };
  return { source_type: "article", all_articles: true };
}

export default function TrainingTab() {
  const [params, setParams] = useSearchParams();
  const [isAdmin, setIsAdmin] = useState(false);
  const pane = parsePane(params.get("tab"), isAdmin);

  const [sources, setSources] = useState<TrainingSources | null>(null);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<TrainingSessionState | null>(null);
  const [view, setView] = useState<TrainView>({ kind: "picker" });
  const [startingKey, setStartingKey] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((me) => {
        if (!cancelled) setIsAdmin(Boolean(me.is_support_admin));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const loadPicker = useCallback(async () => {
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const [src, active] = await Promise.all([fetchTrainingSources(), fetchActiveTrainingSession()]);
      setSources(src);
      setActiveSession(active);
    } catch (e) {
      setSourcesError(e instanceof Error ? e.message : "Не удалось загрузить источники вопросов");
    } finally {
      setSourcesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPicker();
  }, [loadPicker]);

  function setPane(next: Pane) {
    const p = new URLSearchParams(params);
    if (next === "train") p.delete("tab");
    else p.set("tab", next);
    setParams(p, { replace: true });
  }

  const start = useCallback(async (choice: TrainingStartChoice, key: string) => {
    setStartingKey(key);
    setStartError(null);
    try {
      const session = await startTrainingSession(choice);
      setActiveSession(session);
      setView({ kind: "running", session });
    } catch (e) {
      setStartError(e instanceof Error ? e.message : "Не удалось начать тренировку");
      setView({ kind: "picker" });
    } finally {
      setStartingKey(null);
    }
  }, []);

  const onEnded = useCallback((session: TrainingSessionState, notice?: string, completed?: boolean) => {
    setActiveSession(null);
    setView({ kind: "summary", session, notice, completed });
  }, []);

  const running = view.kind === "running";

  return (
    <div className="tp on stats-page trn-page">
      <div className="pg stats-page__inner trn-page__inner">
        <header className="trn-page__header">
          <div>
            <h1 className="stats-page__title">Тренажёр</h1>
            <p className="trn-page__subtitle">
              Отвечайте на вопросы из базы знаний сколько угодно: ошибки не влияют на тесты статей и ежедневный тест.
            </p>
          </div>
        </header>

        <div className="stats-pane-tabs" role="tablist" aria-label="Разделы тренажёра">
          <button
            type="button"
            role="tab"
            aria-selected={pane === "train"}
            className={`stats-pane-tab${pane === "train" ? " on" : ""}`}
            onClick={() => setPane("train")}
          >
            {running ? "Тренировка · идёт" : "Тренировка"}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={pane === "history"}
            className={`stats-pane-tab${pane === "history" ? " on" : ""}`}
            onClick={() => setPane("history")}
          >
            Моя история
          </button>
          {isAdmin ? (
            <button
              type="button"
              role="tab"
              aria-selected={pane === "team"}
              className={`stats-pane-tab${pane === "team" ? " on" : ""}`}
              onClick={() => setPane("team")}
            >
              Статистика команды
            </button>
          ) : null}
        </div>

        {/* Раннер остаётся смонтированным при переключении вкладок, чтобы не терять состояние вопроса. */}
        <div hidden={pane !== "train"}>
          {startError ? (
            <div className="trn-alert" role="alert">
              {startError}
            </div>
          ) : null}
          {view.kind === "running" ? (
            <TrainingRunner key={view.session.id} session={view.session} onEnded={onEnded} active={pane === "train"} />
          ) : view.kind === "summary" ? (
            <TrainingSummary
              session={view.session}
              notice={view.notice}
              completed={view.completed}
              onRestart={() => void start(choiceFromSession(view.session), "restart")}
              onPickAnother={() => {
                setView({ kind: "picker" });
                void loadPicker();
              }}
              onHistory={() => setPane("history")}
            />
          ) : (
            <TrainingSourcePicker
              sources={sources}
              loading={sourcesLoading}
              error={sourcesError}
              activeSession={activeSession}
              startingKey={startingKey}
              onStart={(choice, key) => void start(choice, key)}
              onResume={() => {
                if (activeSession) setView({ kind: "running", session: activeSession });
              }}
              onRetry={() => void loadPicker()}
            />
          )}
        </div>

        {pane === "history" ? <TrainingHistory key={view.kind} onStartTraining={() => setPane("train")} /> : null}
        {pane === "team" && isAdmin ? <TrainingAdminPanel /> : null}
      </div>
    </div>
  );
}
