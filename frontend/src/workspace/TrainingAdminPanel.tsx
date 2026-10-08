import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchTrainingAdminLeaders,
  fetchTrainingAdminOperatorSessions,
  fetchTrainingAdminOperators,
  fetchTrainingAdminSummary,
  type TrainingAdminOperatorRow,
  type TrainingAdminOperatorSessions,
  type TrainingAdminOperators,
  type TrainingAdminSummary,
  type TrainingLeaders as TrainingLeadersData,
  type TrainingPeriod,
} from "@/api/training";
import { quizScoreClass } from "@/api/statsQuizTraining";
import DatePickerField from "@/components/DatePickerField";
import {
  defaultStatsPeriod,
  detectStatsPeriodPreset,
  statsPeriodForPreset,
  todayYmd,
  type StatsPeriodPreset,
} from "@/utils/formatDuration";
import { quizScoreBarStyle } from "@/workspace/dailyQuizScore";
import TrainingLeaders from "@/workspace/TrainingLeaders";
import TrainingSessionsTable from "@/workspace/TrainingSessionsTable";
import {
  formatTrainingDateTime,
  formatTrainingDuration,
  pluralRu,
} from "@/workspace/trainingFormat";

const PRESETS: { key: Exclude<StatsPeriodPreset, "custom">; label: string }[] = [
  { key: "month", label: "Этот месяц" },
  { key: "7d", label: "7 дней" },
  { key: "30d", label: "30 дней" },
  { key: "year", label: "Год" },
];

const SESSIONS_PER_PAGE = 10;

type Loadable<T> = { data: T | null; loading: boolean; error: string | null };

function useLoadable<T>(loader: () => Promise<T>, deps: unknown[]): Loadable<T> & { reload: () => void } {
  const [state, setState] = useState<Loadable<T>>({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    loader()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setState({ data: null, loading: false, error: e instanceof Error ? e.message : "Не удалось загрузить данные" });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}

function OperatorSessions({ operator, period }: { operator: TrainingAdminOperatorRow; period: TrainingPeriod }) {
  const [data, setData] = useState<TrainingAdminOperatorSessions | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchTrainingAdminOperatorSessions(operator.operator_id, period, 1, SESSIONS_PER_PAGE));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить сессии");
    } finally {
      setLoading(false);
    }
  }, [operator.operator_id, period]);

  useEffect(() => {
    void load();
  }, [load]);

  async function loadMore() {
    if (!data) return;
    setLoadingMore(true);
    try {
      const page = await fetchTrainingAdminOperatorSessions(operator.operator_id, period, data.page + 1, SESSIONS_PER_PAGE);
      setData({ ...page, items: [...data.items, ...page.items] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить сессии");
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading) return <div className="trn-expand__state">Загрузка сессий…</div>;
  if (error && !data) {
    return (
      <div className="trn-expand__state trn-state--error">
        {error}{" "}
        <button type="button" className="stats-op-link" onClick={() => void load()}>
          Повторить
        </button>
      </div>
    );
  }
  if (!data || data.items.length === 0) {
    return <div className="trn-expand__state">За выбранный период сессий нет.</div>;
  }
  return (
    <div className="trn-expand__body">
      <TrainingSessionsTable items={data.items} compact />
      {data.items.length < data.total ? (
        <div className="trn-more">
          <button type="button" className="kb-quiz-btn-secondary" disabled={loadingMore} onClick={() => void loadMore()}>
            {loadingMore ? "Загрузка…" : `Показать ещё (${data.total - data.items.length})`}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function OperatorsTable({ data, period }: { data: TrainingAdminOperators; period: TrainingPeriod }) {
  const [expanded, setExpanded] = useState<Set<number>>(() => new Set());

  const rows = useMemo(
    () =>
      [...data.items].sort((a, b) => {
        const aa = a.total_answers > 0 ? 0 : 1;
        const bb = b.total_answers > 0 ? 0 : 1;
        if (aa !== bb) return aa - bb;
        return a.operator_name.localeCompare(b.operator_name, "ru");
      }),
    [data.items],
  );

  useEffect(() => {
    setExpanded(new Set());
  }, [period.dateFrom, period.dateTo]);

  function toggle(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (rows.length === 0) {
    return <div className="trn-state">Нет подчинённых операторов.</div>;
  }

  return (
    <div className="stats-table-wrap">
      <table className="dt stats-table trn-table trn-ops-table">
        <thead>
          <tr>
            <th>Сотрудник</th>
            <th className="trn-num">Сессий</th>
            <th className="trn-num">Ответы</th>
            <th>Результат</th>
            <th className="trn-num">Охват</th>
            <th className="trn-num">Время</th>
            <th>Последний ответ</th>
            <th aria-label="Развернуть" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const open = expanded.has(row.operator_id);
            const idle = row.total_answers === 0;
            return (
              <Fragment key={row.operator_id}>
                <tr
                  className={`trn-op-row${open ? " is-open" : ""}${idle ? " is-idle" : ""}`}
                  onClick={() => toggle(row.operator_id)}
                >
                  <td>
                    <button
                      type="button"
                      className="stats-op-link trn-op-name"
                      aria-expanded={open}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggle(row.operator_id);
                      }}
                    >
                      {row.has_active_session ? (
                        <span className="trn-live-dot" title="Сейчас тренируется" aria-label="Сейчас тренируется" />
                      ) : null}
                      {row.operator_name}
                    </button>
                  </td>
                  <td className="trn-num">{row.sessions_count || "—"}</td>
                  <td className="trn-num">
                    {idle ? (
                      "—"
                    ) : (
                      <>
                        <span className="trn-ok-text">{row.correct_count}</span>
                        <span className="trn-cell-sub"> / {row.total_answers}</span>
                      </>
                    )}
                  </td>
                  <td>
                    {row.score_percent != null ? (
                      <div className="trn-score-cell">
                        <span className={quizScoreClass(row.score_percent)}>{Math.round(row.score_percent)}%</span>
                        <span className="trn-minibar" aria-hidden>
                          <span style={quizScoreBarStyle(row.score_percent)} />
                        </span>
                      </div>
                    ) : (
                      <span className="trn-cell-sub">не тренировался</span>
                    )}
                  </td>
                  <td className="trn-num">{row.coverage || "—"}</td>
                  <td className="trn-num">{formatTrainingDuration(row.total_duration_sec)}</td>
                  <td className="trn-cell-sub">{row.last_activity_at ? formatTrainingDateTime(row.last_activity_at) : "—"}</td>
                  <td className="trn-chev-cell">
                    <svg className={`trn-chev${open ? " is-open" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                      <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </td>
                </tr>
                {open ? (
                  <tr className="trn-expand">
                    <td colSpan={8}>
                      <OperatorSessions operator={row} period={period} />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function TrainingAdminPanel() {
  const initial = defaultStatsPeriod();
  const [dateFrom, setDateFrom] = useState(initial.from);
  const [dateTo, setDateTo] = useState(initial.to);
  const [preset, setPreset] = useState<StatsPeriodPreset>("month");
  const todayMax = todayYmd();
  const period = useMemo<TrainingPeriod>(() => ({ dateFrom, dateTo }), [dateFrom, dateTo]);
  const periodValid = Boolean(dateFrom && dateTo && dateFrom <= dateTo);

  const guard = <T,>(fn: () => Promise<T>) => (periodValid ? fn() : Promise.reject(new Error("Укажите корректный период")));
  const summary = useLoadable<TrainingAdminSummary>(() => guard(() => fetchTrainingAdminSummary(period)), [period]);
  const leaders = useLoadable<TrainingLeadersData>(() => guard(() => fetchTrainingAdminLeaders(period)), [period]);
  const operators = useLoadable<TrainingAdminOperators>(() => guard(() => fetchTrainingAdminOperators(period)), [period]);

  function applyPreset(p: Exclude<StatsPeriodPreset, "custom">) {
    const r = statsPeriodForPreset(p);
    setDateFrom(r.from);
    setDateTo(r.to);
    setPreset(p);
  }

  function onFrom(v: string) {
    setDateFrom(v);
    setPreset(v && dateTo ? detectStatsPeriodPreset(v, dateTo) : "custom");
  }

  function onTo(v: string) {
    setDateTo(v);
    setPreset(dateFrom && v ? detectStatsPeriodPreset(dateFrom, v) : "custom");
  }

  const s = summary.data;

  return (
    <div className="trn-admin">
      <div className="stats-page__toolbar">
        <div className="stats-page__filters">
          <div className="stats-page__period">
            <span className="stats-page__filter-label">Период ответов</span>
            <div className="stats-page__presets" role="group" aria-label="Быстрый выбор периода">
              {PRESETS.map((p) => (
                <button
                  key={p.key}
                  type="button"
                  className={`stats-preset${preset === p.key ? " on" : ""}`}
                  onClick={() => applyPreset(p.key)}
                >
                  {p.label}
                </button>
              ))}
            </div>
            <div className="stats-page__date-range">
              <div className="stats-page__date-field">
                <span className="stats-page__date-cap">С</span>
                <DatePickerField
                  className="stats-page__dp"
                  calendarClassName="stats-page__dp-cal"
                  value={dateFrom}
                  maxDate={dateTo || todayMax}
                  onChange={onFrom}
                  placeholder="дд.мм.гггг"
                />
              </div>
              <span className="stats-page__dash" aria-hidden>
                —
              </span>
              <div className="stats-page__date-field">
                <span className="stats-page__date-cap">По</span>
                <DatePickerField
                  className="stats-page__dp"
                  calendarClassName="stats-page__dp-cal"
                  value={dateTo}
                  minDate={dateFrom || undefined}
                  maxDate={todayMax}
                  onChange={onTo}
                  placeholder="дд.мм.гггг"
                />
              </div>
            </div>
          </div>
        </div>

        {summary.loading ? (
          <div className="stats-metrics stats-metrics--admin stats-metrics--placeholder trn-kpis" aria-busy="true">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="stats-m-card stats-m-card--skeleton" />
            ))}
          </div>
        ) : s ? (
          <div className="stats-metrics stats-metrics--admin trn-kpis">
            <div
              className="stats-m-card"
              data-tip="Доля верных ответов всех подчинённых за период: сумма верных / сумма ответов"
            >
              <div className="stats-m-label">Средний результат</div>
              <div className={`stats-m-val ${s.total_answers > 0 ? quizScoreClass(s.avg_score_percent) : ""}`}>
                {s.total_answers > 0 ? `${Math.round(s.avg_score_percent)}%` : "—"}
              </div>
              <div className="trn-kpi-hint">
                {s.active_operators_count} из {s.operators_count}{" "}
                {pluralRu(s.operators_count, "сотрудника", "сотрудников", "сотрудников")} тренировались
              </div>
            </div>
            <div className="stats-m-card" data-tip="Сессии, в которых есть ответы за период">
              <div className="stats-m-label">Сессий</div>
              <div className="stats-m-val">{s.sessions_count}</div>
            </div>
            <div className="stats-m-card" data-tip="Охват — сколько разных вопросов затронуто">
              <div className="stats-m-label">Ответов</div>
              <div className="stats-m-val">{s.total_answers}</div>
              <div className="trn-kpi-hint">охват {s.coverage} {pluralRu(s.coverage, "вопрос", "вопроса", "вопросов")}</div>
            </div>
            <div className="stats-m-card" data-tip="Сумма длительностей сессий: от старта до последнего ответа">
              <div className="stats-m-label">Суммарное время</div>
              <div className="stats-m-val">{formatTrainingDuration(s.total_duration_sec)}</div>
            </div>
          </div>
        ) : null}
      </div>

      {summary.error ? (
        <div className="stats-page__state stats-page__state--error">
          {summary.error}{" "}
          <button type="button" className="stats-op-link" onClick={summary.reload}>
            Повторить
          </button>
        </div>
      ) : null}

      <TrainingLeaders data={leaders.data} loading={leaders.loading} error={leaders.error} />

      <div className="card stats-card">
        <div className="stats-card__title">Сотрудники</div>
        {operators.loading ? (
          <div className="trn-skeleton trn-skeleton--table" aria-busy="true" />
        ) : operators.error ? (
          <div className="trn-state trn-state--error">
            {operators.error}{" "}
            <button type="button" className="stats-op-link" onClick={operators.reload}>
              Повторить
            </button>
          </div>
        ) : operators.data ? (
          <OperatorsTable data={operators.data} period={period} />
        ) : null}
      </div>
    </div>
  );
}
