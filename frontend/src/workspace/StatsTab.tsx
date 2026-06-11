import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAuthMe } from "@/api/auth";
import { ticketsListUrl } from "@/api/operatorProfile";
import {
  fetchStatsDashboard,
  type OperatorStatsRow,
  type StatsDashboard,
  type StatsRatingItem,
} from "@/api/stats";
import DatePickerField from "@/components/DatePickerField";
import {
  defaultStatsPeriod,
  detectStatsPeriodPreset,
  formatDurationSec,
  formatRating,
  statsPeriodForPreset,
  todayYmd,
  type StatsPeriodPreset,
} from "@/utils/formatDuration";
import { ratingToneClass } from "@/utils/ratingTone";

function formatRatedDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

function operatorStatus(row: OperatorStatsRow): { label: string; kind: "good" | "bad" | "neutral" } {
  const rating = row.avg_rating;
  const speed = row.avg_first_response_sec;
  if (rating != null && rating < 4) return { label: "Нужна помощь", kind: "bad" };
  if (speed != null && speed > 600) return { label: "Медленный ответ", kind: "bad" };
  if (rating != null && rating >= 4.8 && (row.closed_tickets ?? 0) >= 10) {
    return { label: "Лидер смены", kind: "good" };
  }
  return { label: "В норме", kind: "neutral" };
}

type MetricCard = {
  label: string;
  value: string;
  hint?: string;
  valueClass?: string;
  linkTo?: string;
};

function buildMetrics(summary: StatsDashboard["summary"]): MetricCard[] {
  return [
    {
      label: "Новые тикеты",
      value: String(summary.new_tickets),
      hint: "Созданы за выбранный период",
    },
    {
      label: "Время реакции",
      value: formatDurationSec(summary.avg_first_response_sec),
      hint: "Среднее время до первого ответа оператора",
    },
    {
      label: "Закрыто",
      value: String(summary.closed_tickets),
      hint: "Тикеты, закрытые за период",
    },
    {
      label: "Средняя оценка",
      value: formatRating(summary.avg_rating),
      hint: "Оценки абонентов по закрытым тикетам",
      valueClass: ratingToneClass(summary.avg_rating),
    },
    {
      label: "Время жизни",
      value: formatDurationSec(summary.avg_lifetime_sec),
      hint: "Среднее время от создания до закрытия",
    },
  ];
}

export default function StatsTab() {
  const initial = defaultStatsPeriod();
  const [dateFrom, setDateFrom] = useState(initial.from);
  const [dateTo, setDateTo] = useState(initial.to);
  const [periodPreset, setPeriodPreset] = useState<StatsPeriodPreset>("month");
  const [operatorId, setOperatorId] = useState<number | "all">("all");
  const todayMax = todayYmd();
  const [data, setData] = useState<StatsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewerName, setViewerName] = useState("Оператор");
  const [viewerUserId, setViewerUserId] = useState<number | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((me) => {
        if (cancelled) return;
        setViewerName(me.full_name?.trim() || me.login?.trim() || "Оператор");
        setViewerUserId(me.user_id);
        setIsAdmin(Boolean(me.is_support_admin));
      })
      .catch(() => {
        if (!cancelled) setViewerName("Оператор");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchStatsDashboard({
      dateFrom,
      dateTo,
      operatorId: operatorId === "all" ? null : operatorId,
    })
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(e instanceof Error ? e.message : "Не удалось загрузить статистику");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [dateFrom, dateTo, operatorId]);

  function applyPreset(preset: Exclude<StatsPeriodPreset, "custom">) {
    const p = statsPeriodForPreset(preset);
    setDateFrom(p.from);
    setDateTo(p.to);
    setPeriodPreset(preset);
  }

  function onDateFromChange(v: string) {
    setDateFrom(v);
    if (v && dateTo) setPeriodPreset(detectStatsPeriodPreset(v, dateTo));
    else setPeriodPreset("custom");
  }

  function onDateToChange(v: string) {
    setDateTo(v);
    if (dateFrom && v) setPeriodPreset(detectStatsPeriodPreset(dateFrom, v));
    else setPeriodPreset("custom");
  }

  const metrics = useMemo(() => {
    if (!data) return [];
    const closedLink =
      dateFrom && dateTo
        ? ticketsListUrl({
            closed: true,
            dateFrom,
            dateTo,
            assignedTo: isAdmin ? undefined : viewerUserId ?? undefined,
          })
        : undefined;
    return buildMetrics(data.summary).map((m) =>
      m.label === "Закрыто" && closedLink ? { ...m, linkTo: closedLink } : m,
    );
  }, [data, dateFrom, dateTo, isAdmin, viewerUserId]);
  const adminAllView = isAdmin && operatorId === "all";
  const title = adminAllView ? "Общая аналитика КЦ" : "Личная статистика";
  const subtitle = adminAllView
    ? `Мониторинг операторов · ${data?.operator_options.length ?? 0} сотрудников`
    : `Оператор: ${data?.summary.operator_name || viewerName}`;

  return (
    <div className="tp on stats-page">
      <div className="pg stats-page__inner">
        <header className="stats-page__header">
          <h1 className="stats-page__title">{title}</h1>
          <p className="stats-page__subtitle">{subtitle}</p>
        </header>

        <div className="stats-page__toolbar">
          <div className="stats-page__filters">
            {isAdmin ? (
              <label className="stats-page__filter">
                <span className="stats-page__filter-label">Оператор</span>
                <select
                  className="msl stats-page__select"
                  value={operatorId === "all" ? "all" : String(operatorId)}
                  onChange={(e) => {
                    const v = e.target.value;
                    setOperatorId(v === "all" ? "all" : Number(v));
                  }}
                >
                  <option value="all">Все сотрудники</option>
                  {(data?.operator_options ?? []).map((op) => (
                    <option key={op.id} value={op.id}>
                      {op.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <div className="stats-page__period">
              <span className="stats-page__filter-label">Период</span>
              <div className="stats-page__presets" role="group" aria-label="Быстрый выбор периода">
                <button
                  type="button"
                  className={`stats-preset${periodPreset === "month" ? " on" : ""}`}
                  onClick={() => applyPreset("month")}
                >
                  Этот месяц
                </button>
                <button
                  type="button"
                  className={`stats-preset${periodPreset === "7d" ? " on" : ""}`}
                  onClick={() => applyPreset("7d")}
                >
                  7 дней
                </button>
                <button
                  type="button"
                  className={`stats-preset${periodPreset === "30d" ? " on" : ""}`}
                  onClick={() => applyPreset("30d")}
                >
                  30 дней
                </button>
                <button
                  type="button"
                  className={`stats-preset${periodPreset === "year" ? " on" : ""}`}
                  onClick={() => applyPreset("year")}
                >
                  Год
                </button>
              </div>
              <div className="stats-page__date-range">
                <div className="stats-page__date-field">
                  <span className="stats-page__date-cap">С</span>
                  <DatePickerField
                    className="stats-page__dp"
                    calendarClassName="stats-page__dp-cal"
                    value={dateFrom}
                    maxDate={dateTo || todayMax}
                    onChange={onDateFromChange}
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
                    onChange={onDateToChange}
                    placeholder="дд.мм.гггг"
                  />
                </div>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="stats-metrics stats-metrics--placeholder" aria-busy="true">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="stats-m-card stats-m-card--skeleton" />
              ))}
            </div>
          ) : null}
          {!loading && !error && data ? (
            <div className={`stats-metrics${adminAllView ? " stats-metrics--admin" : ""}`}>
              {metrics.map((m) =>
                m.linkTo ? (
                  <Link
                    key={m.label}
                    to={m.linkTo}
                    className="stats-m-card stats-m-card--link"
                    data-tip={m.hint}
                    title={m.hint}
                  >
                    <div className="stats-m-label">{m.label}</div>
                    <div className={`stats-m-val${m.valueClass ? ` ${m.valueClass}` : ""}`}>
                      {m.value}
                    </div>
                  </Link>
                ) : (
                  <div key={m.label} className="stats-m-card" data-tip={m.hint}>
                    <div className="stats-m-label">{m.label}</div>
                    <div className={`stats-m-val${m.valueClass ? ` ${m.valueClass}` : ""}`}>
                      {m.value}
                    </div>
                  </div>
                ),
              )}
            </div>
          ) : null}
        </div>

        {error ? <div className="stats-page__state stats-page__state--error">{error}</div> : null}

        {!loading && !error && data ? (
          <>
            {adminAllView && data.operators.length > 0 ? (
              <div className="card stats-card">
                <div className="stats-card__title">Сравнительная таблица операторов</div>
                <div className="stats-table-wrap">
                  <table className="dt stats-table">
                    <thead>
                      <tr>
                        <th>Место</th>
                        <th>Сотрудник</th>
                        <th>Новые</th>
                        <th>Закрыто</th>
                        <th>Скорость</th>
                        <th>Оценка</th>
                        <th>Время жизни</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.operators.map((row, idx) => {
                        const st = operatorStatus(row);
                        return (
                          <tr key={row.operator_id} className={st.kind === "bad" ? "stats-table__row--warn" : ""}>
                            <td>
                              <span className={`stats-rank${idx === 0 ? " stats-rank--top" : ""}`}>{idx + 1}</span>
                            </td>
                            <td>
                              <button
                                type="button"
                                className="stats-op-link"
                                onClick={() => setOperatorId(row.operator_id)}
                              >
                                {row.operator_name}
                              </button>
                            </td>
                            <td>{row.new_tickets}</td>
                            <td>{row.closed_tickets}</td>
                            <td>{formatDurationSec(row.avg_first_response_sec)}</td>
                            <td>
                              <span className={`rating-tone rating-tone--pill ${ratingToneClass(row.avg_rating)}`.trim()}>
                                {formatRating(row.avg_rating)}
                              </span>
                            </td>
                            <td>{formatDurationSec(row.avg_lifetime_sec)}</td>
                            <td>
                              <span className={`stats-status stats-status--${st.kind}`}>{st.label}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}

            {data.recent_ratings.length > 0 ? (
              <div className="card stats-card">
                <div className="stats-card__title">Обратная связь от абонентов</div>
                <div className="stats-table-wrap">
                  <table className="dt stats-table">
                    <thead>
                      <tr>
                        <th>Тикет</th>
                        <th>Канал</th>
                        <th>Категория</th>
                        <th>Дата</th>
                        <th>Время решения</th>
                        <th>Инженер</th>
                        <th style={{ textAlign: "right" }}>Балл</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_ratings.map((r: StatsRatingItem) => (
                        <tr key={`${r.ticket_id}-${r.rated_at}`}>
                          <td>
                            <Link to={`/tickets/${r.ticket_id}`} className="stats-ticket-link">
                              #{r.ticket_id}
                            </Link>
                          </td>
                          <td>{r.source_label}</td>
                          <td>{r.category_label ?? "—"}</td>
                          <td>{formatRatedDate(r.rated_at)}</td>
                          <td>{formatDurationSec(r.lifetime_sec)}</td>
                          <td>
                            <span
                              className={`stats-status stats-status--${r.engineer_involved ? "neutral" : "good"}`}
                              title={
                                r.engineer_involved
                                  ? "Был перевод на 2-ю линию или сообщение инженера в чате"
                                  : "Решено без участия инженера"
                              }
                            >
                              {r.engineer_involved ? "Да" : "Нет"}
                            </span>
                          </td>
                          <td style={{ textAlign: "right" }}>
                            {r.rating != null ? (
                              <span
                                className={`rating-tone rating-tone--pill ${ratingToneClass(r.rating, true)}`.trim()}
                              >
                                {r.rating}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
