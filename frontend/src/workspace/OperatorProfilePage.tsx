import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAuthMe, type AuthMe } from "@/api/auth";
import AdminOperatorsPage from "@/workspace/AdminOperatorsPage";
import {
  clampProfileMonth,
  fetchOperatorTicketStats,
  getDefaultProfilePeriod,
  getProfileMonthOptions,
  getProfileYearOptions,
  profileMonthName,
  ticketsListUrl,
  type OperatorTicketMonthStats,
} from "@/api/operatorProfile";

export default function OperatorProfilePage() {
  const defaultPeriod = useMemo(() => getDefaultProfilePeriod(), []);
  const yearOptions = useMemo(() => getProfileYearOptions(), []);
  const [year, setYear] = useState(defaultPeriod.year);
  const [month, setMonth] = useState(defaultPeriod.month);

  const monthOptions = useMemo(() => getProfileMonthOptions(year), [year]);

  const [me, setMe] = useState<AuthMe | null>(null);
  const [stats, setStats] = useState<OperatorTicketMonthStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const clamped = clampProfileMonth(year, month);
    if (clamped !== month) setMonth(clamped);
  }, [year, month]);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((auth) => {
        if (!cancelled) setMe(auth);
      })
      .catch(() => {
        if (!cancelled) setMe(null);
      })
      .finally(() => {
        if (!cancelled) setAuthChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const isAdmin = Boolean(me?.is_support_admin);

  useEffect(() => {
    if (!authChecked || isAdmin || monthOptions.length === 0) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchOperatorTicketStats(year, month)
      .then((data) => {
        if (!cancelled) setStats(data);
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
  }, [authChecked, isAdmin, year, month, monthOptions.length]);

  if (!authChecked) {
    return (
      <div className="op-page">
        <div className="op-head">
          <h1 className="op-title">Профиль</h1>
        </div>
      </div>
    );
  }

  if (isAdmin) {
    return <AdminOperatorsPage />;
  }

  function onYearChange(nextYear: number) {
    setYear(nextYear);
    setMonth((prev) => clampProfileMonth(nextYear, prev));
  }

  const closedUrl =
    me && stats
      ? ticketsListUrl({
          closed: true,
          assignedTo: me.user_id,
          dateFrom: stats.date_from,
          dateTo: stats.date_to,
        })
      : "#";

  const openUrl =
    me && stats
      ? ticketsListUrl({
          closed: false,
          assignedTo: me.user_id,
          dateFrom: stats.date_from,
          dateTo: stats.date_to,
        })
      : "#";

  const fullName = me?.full_name?.trim() || null;
  const login = me?.login?.trim() || null;
  const displayName = fullName || login || (loading ? "…" : "—");

  return (
    <div className="op-page">
      <div className="op-head">
        <h1 className="op-title">Профиль</h1>
        <p className="op-sub">Ваш аккаунт оператора Helpdesk</p>
      </div>

      <div className="card op-card">
        <div className="op-card-label">Аккаунт</div>
        <div className="op-card-value">{displayName}</div>
        {fullName && login ? <div className="op-card-login">{login}</div> : null}
      </div>

      <div className="card op-card">
        <div className="op-section-head">
          <h2 className="op-section-title">История тикетов</h2>
          <div className="op-period-selects">
            <label className="op-month-label">
              <span>Год</span>
              <select
                className="op-month-select"
                value={year}
                onChange={(e) => onYearChange(Number(e.target.value))}
              >
                {yearOptions.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
            <label className="op-month-label">
              <span>Месяц</span>
              <select
                className="op-month-select"
                value={month}
                disabled={monthOptions.length === 0}
                onChange={(e) => setMonth(Number(e.target.value))}
              >
                {monthOptions.map((m) => (
                  <option key={m} value={m}>
                    {profileMonthName(m)}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {monthOptions.length === 0 ? (
          <div className="op-error">Нет доступных месяцев для выбранного года</div>
        ) : null}
        {error ? <div className="op-error">{error}</div> : null}

        <div className="op-stats-grid">
          <div className="op-stat-card">
            <div className="op-stat-label">Открытые за период</div>
            <div className="op-stat-value">{loading ? "…" : (stats?.open_count ?? 0)}</div>
            <div className="op-stat-hint">Созданы в выбранном месяце</div>
            {!loading && stats && stats.open_count > 0 ? (
              <Link className="op-stat-link" to={openUrl}>
                Смотреть список →
              </Link>
            ) : null}
          </div>

          <div className="op-stat-card">
            <div className="op-stat-label">Закрытые за период</div>
            <div className="op-stat-value">{loading ? "…" : (stats?.closed_count ?? 0)}</div>
            <div className="op-stat-hint">Закрыты в выбранном месяце</div>
            {!loading && stats && stats.closed_count > 0 ? (
              <Link className="op-stat-link" to={closedUrl}>
                Смотреть список →
              </Link>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
