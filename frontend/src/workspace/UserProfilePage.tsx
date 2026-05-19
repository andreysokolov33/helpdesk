import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteFreezePlan,
  fetchUserProfile,
  postDisconnect,
  postFreeze,
  postUnarchive,
  postUnfreeze,
  type ProfileTariff,
  type UserProfileResponse,
} from "@/api/userProfile";
import { copyPhone, formatPhoneDisplay } from "@/utils/phone";
import { AuthPageHelp } from "@/components/AuthPageHelp";
import { categoryBadgeClass, supportLineBadgeClass, supportLineLabel } from "@/utils/ticketLabels";

type ModalKind = "unfreeze" | "unarchive" | "disconnect" | "freeze" | null;

const REPORTS = [
  { id: "check", label: "Быстрая проверка пользователя" },
  { id: "payments", label: "История платежей" },
  { id: "tariffs", label: "История подключенных тарифов" },
] as const;

function fmtMoney(n: number) {
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₽`;
}

function fmtDt(iso: string) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtTrafficMb(n: number) {
  return n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

function statusClass(us: number | null) {
  if (us === 3) return "up-badge arch";
  if (us === 2) return "up-badge frz";
  return "up-badge ok";
}

function entityClass(isJuridical: number) {
  return isJuridical === 2 ? "up-badge jur" : "up-badge phys";
}

function PhoneValue({ phone }: { phone: string | null }) {
  if (!phone) return <span className="up-v">—</span>;
  const display = formatPhoneDisplay(phone);
  return (
    <button
      type="button"
      className="up-phone-btn up-v"
      title="Скопировать номер"
      onClick={() => void copyPhone(phone)}
    >
      {display}
    </button>
  );
}


function ProfileSideColumn({
  balance,
  authPage,
  onResetPassword,
}: {
  balance: number;
  authPage: string | null;
  onResetPassword: () => void;
}) {
  return (
    <div className="up-tariff-side">
      <div className="card up-card up-metric-cell up-balance-cell">
        <div className="ct">Баланс</div>
        <div className={`up-metric-val up-balance-val ${balance < 0 ? "bad" : ""}`}>{fmtMoney(balance)}</div>
      </div>
      <div className="card up-card up-metric-cell up-auth-cell">
        <div className="up-metric-head">
          <span className="ct">Страница авторизации</span>
          <AuthPageHelp hotspotAddress={authPage} />
        </div>
        <div className="up-metric-val up-auth-val">{authPage ?? "—"}</div>
      </div>
      <button type="button" className="up-btn sec up-reset-pwd" onClick={onResetPassword}>
        Сбросить пароль
      </button>
    </div>
  );
}

function TariffCard({
  tariff,
  netflowNote,
  netflowTariff,
  onFreeze,
  onUnfreeze,
  onCancelPlan,
  openSessionsCount,
  onDisconnect,
}: {
  tariff: ProfileTariff | null;
  netflowNote: string | null;
  netflowTariff: string | null;
  openSessionsCount: number;
  onFreeze: () => void;
  onUnfreeze: () => void;
  onCancelPlan: () => void;
  onDisconnect: () => void;
}) {
  if (!tariff && !netflowTariff) {
    return (
      <div className="card up-card up-tariff up-tariff-main">
        <div className="ct">Тарифный план</div>
        <p className="up-muted">Тариф не подключён</p>
      </div>
    );
  }

  return (
    <div className="card up-card up-tariff up-tariff-main">
      <div className="up-card-head">
        <div className="ct">Тарифный план</div>
        <div className="up-actions">
          {tariff?.can_unfreeze ? (
            <button type="button" className="up-btn pri" onClick={onUnfreeze}>
              Разморозить
            </button>
          ) : null}
          {tariff?.can_freeze ? (
            <button type="button" className="up-btn sec" onClick={onFreeze}>
              Заморозить
            </button>
          ) : null}
          {tariff?.can_cancel_planned_freeze ? (
            <button type="button" className="up-btn sec" onClick={onCancelPlan}>
              Отменить заморозку
            </button>
          ) : null}
          {tariff?.can_disconnect_sessions !== false ? (
            openSessionsCount > 0 ? (
              <button type="button" className="up-btn sec" onClick={onDisconnect}>
                Закрыть сессии ({openSessionsCount})
              </button>
            ) : (
              <span className="up-sessions-hint">Активных сессий на данной УЗ нет</span>
            )
          ) : null}
        </div>
      </div>

      {netflowNote ? <div className="up-alert info">{netflowNote}</div> : null}
      {netflowTariff ? (
        <div className="up-kv">
          <span className="up-k">Тариф (Netflow)</span>
          <span className="up-v">{netflowTariff}</span>
        </div>
      ) : null}

      {tariff?.state === "planned_freeze" ? (
        <div className="up-alert warn">
          Планируемая заморозка: {tariff.planned_freeze_at}
          {tariff.unfreeze_at ? ` · разморозка ${tariff.unfreeze_at}` : ""}
        </div>
      ) : null}

      {tariff?.state === "frozen" ? (
        <div className="up-freeze-box">
          <div className="up-freeze-title">Тариф заморожен</div>
          {tariff.frozen_at ? <div>Заморожен: {tariff.frozen_at}</div> : null}
          {tariff.unfreeze_at ? <div>Дата разморозки: <strong>{tariff.unfreeze_at}</strong></div> : null}
          {tariff.frozen_remaining_label ? (
            <div>Замороженный срок: {tariff.frozen_remaining_label}</div>
          ) : null}
        </div>
      ) : null}

      {tariff ? (
        <>
          <div className="up-kv">
            <span className="up-k">Название</span>
            <span className="up-v">{tariff.tariff_name}</span>
          </div>
          <div className="up-kv">
            <span className="up-k">Статус</span>
            <span className={`up-v ${tariff.is_active ? "ok" : "bad"}`}>
              {tariff.is_active ? "Активен" : "Неактивен"}
            </span>
          </div>
          <div className="up-kv">
            <span className="up-k">Обратный канал ↑</span>
            <span className="up-v">{tariff.rate_up}</span>
          </div>
          <div className="up-kv">
            <span className="up-k">Прямой канал ↓</span>
            <span className="up-v">{tariff.rate_down}</span>
          </div>
          <div className="up-kv">
            <span className="up-k">{tariff.speed_unlimited ? "Суточный трафик (остаток / лимит)" : "Трафик (остаток / всего)"}</span>
            <span className={`up-v ${tariff.overrun_mb ? "bad" : ""}`}>
              {fmtTrafficMb(tariff.remain_traffic_mb)} / {fmtTrafficMb(tariff.full_packet_mb)} МБ
            </span>
          </div>
          {tariff.disconnect_at_label ? (
            <div className="up-kv">
              <span className="up-k">Отключение тарифа</span>
              <span className="up-v">
                {tariff.disconnect_at_label}
                {tariff.valid_date_label ? (
                  <span className="up-kv-sub"> · до {tariff.valid_date_label}</span>
                ) : null}
              </span>
            </div>
          ) : null}
          {tariff.jur_main_packet_mb != null ? (
            <div className="up-kv">
              <span className="up-k">Основной пакет (ЮЛ)</span>
              <span className="up-v">{tariff.jur_main_packet_mb.toLocaleString("ru-RU")} МБ</span>
            </div>
          ) : null}
          {tariff.jur_dop_packet_mb != null ? (
            <div className="up-kv">
              <span className="up-k">Доп. пакет (ЮЛ)</span>
              <span className="up-v">{tariff.jur_dop_packet_mb.toLocaleString("ru-RU")} МБ</span>
            </div>
          ) : null}
          {tariff.overrun_mb != null && tariff.overrun_mb > 0 ? (
            <div className="up-alert bad">Перерасход трафика: ~{tariff.overrun_mb.toFixed(1)} МБ</div>
          ) : null}
          {tariff.speed_unlimited && tariff.msk_reset ? (
            <>
              <div className="up-kv">
                <span className="up-k">Сброс суточного трафика</span>
                <span className="up-v">{tariff.msk_reset}</span>
              </div>
              <div className="up-kv">
                <span className="up-k">Местное время (по МСК)</span>
                <span className="up-v">{tariff.local_reset}</span>
              </div>
              {tariff.traffic_renew_count != null ? (
                <div className="up-kv">
                  <span className="up-k">Сбросов доступно</span>
                  <span className="up-v">{tariff.traffic_renew_count}</span>
                </div>
              ) : null}
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default function UserProfilePage() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const uid = Number(userId);
  const [data, setData] = useState<UserProfileResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<(typeof REPORTS)[number]["id"]>("check");
  const [modal, setModal] = useState<ModalKind>(null);
  const [freezeDate, setFreezeDate] = useState("");
  const [unfreezeDate, setUnfreezeDate] = useState("");
  const [showUnfreezeDate, setShowUnfreezeDate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const reload = useCallback(() => {
    if (!Number.isFinite(uid)) return;
    setLoading(true);
    fetchUserProfile(uid)
      .then(setData)
      .catch((e: unknown) => setErr(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setLoading(false));
  }, [uid]);

  useEffect(() => {
    reload();
  }, [reload]);

  async function runAction(fn: () => Promise<{ message: string }>) {
    setBusy(true);
    try {
      const r = await fn();
      setToast(r.message);
      setModal(null);
      reload();
    } catch (e: unknown) {
      setToast(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  if (!Number.isFinite(uid)) {
    return <div className="pg">Некорректный ID абонента</div>;
  }

  if (loading && !data) {
    return (
      <div className="tp on">
        <div className="pg up-loading">Загрузка карточки…</div>
      </div>
    );
  }

  if (err || !data) {
    return (
      <div className="tp on">
        <div className="pg">
          <div className="card">
            <div className="ct">Ошибка</div>
            <p>{err ?? "Нет данных"}</p>
            <Link to="/">← На главную</Link>
          </div>
        </div>
      </div>
    );
  }

  const p = data.personal;
  const idDocLabel = p.is_juridical === 2 ? "ИНН" : "Паспорт";

  return (
    <div className="tp on up-page">
      <div className="pg">
        <div className="up-top">
          <Link to="/" className="up-back">
            ← Поиск
          </Link>
          <h1 className="up-title">{p.name}</h1>
          <div className="up-top-meta">
            <span className={statusClass(p.user_status)}>{p.status_label}</span>
            <span className={entityClass(p.is_juridical)}>{p.entity_label}</span>
            <span className={`up-online-pill ${data.online.is_online ? "on" : "off"}`}>
              {data.online.is_online ? "В сети" : "Офлайн"}
            </span>
            {!data.online.is_online && data.online.last_session_end_label ? (
              <span className="up-session-meta">последняя сессия {data.online.last_session_end_label}</span>
            ) : null}
          </div>
        </div>

        {toast ? (
          <div className="up-toast" role="status">
            {toast}
            <button type="button" aria-label="Закрыть" onClick={() => setToast(null)}>
              ×
            </button>
          </div>
        ) : null}

        <div className="up-stack">
        <div className="up-grid">
            <div className="card up-card up-personal">
              <div className="ct">Персональные данные</div>
              <div className="up-ids">
                <div className="up-id-block">
                  <span className="up-id-lbl">ID</span>
                  <span className="up-id-val up-id-val--num">{p.user_id}</span>
                </div>
                <div className="up-id-block up-id-block--login">
                  <span className="up-id-lbl">Логин</span>
                  <span className="up-id-val up-id-val--login" title={p.login || undefined}>
                    {p.login || "—"}
                  </span>
                </div>
              </div>
              <div className="up-kv">
                <span className="up-k">Почта</span>
                <span className="up-v">{p.email ?? "—"}</span>
              </div>
              <div className="up-kv">
                <span className="up-k">Телефон</span>
                <PhoneValue phone={p.phone} />
              </div>
              <div className="up-kv">
                <span className="up-k">{idDocLabel}</span>
                <span className="up-v">{p.id_doc ?? "—"}</span>
              </div>
              <div className="up-kv">
                <span className="up-k">Станция</span>
                <span className="up-v">{p.station_name ?? "—"}</span>
              </div>
              {p.user_status === 3 ? (
                <button
                  type="button"
                  className="up-btn pri"
                  style={{ marginTop: 10 }}
                  onClick={() => setModal("unarchive")}
                >
                  Разархивировать УЗ
                </button>
              ) : null}
            </div>

            <div className="up-tariff-layout">
              <TariffCard
                tariff={data.tariff}
                netflowNote={data.netflow_note}
                netflowTariff={data.netflow_tariff}
                openSessionsCount={data.open_sessions_count}
                onFreeze={() => {
                  setFreezeDate("");
                  setUnfreezeDate("");
                  setShowUnfreezeDate(false);
                  setModal("freeze");
                }}
                onUnfreeze={() => setModal("unfreeze")}
                onCancelPlan={() => runAction(() => deleteFreezePlan(uid))}
                onDisconnect={() => data.open_sessions_count > 0 && setModal("disconnect")}
              />
              <ProfileSideColumn
                balance={data.balance}
                authPage={p.auth_page}
                onResetPassword={() => setToast("Сброс пароля — в разработке")}
              />
            </div>

            <div className="card up-card up-stats">
              <div className="ct">Статистика</div>
              <select
                className="up-select"
                value={report}
                onChange={(e) => setReport(e.target.value as (typeof REPORTS)[number]["id"])}
              >
                {REPORTS.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
              <div className="up-stub">
                {report === "check" ? (
                  <ul className="up-check-list">
                    {data.health_check.items.map((t) => (
                      <li key={t}>{t}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="up-muted">Раздел «{REPORTS.find((x) => x.id === report)?.label}» — скоро</p>
                )}
              </div>
            </div>
        </div>
        </div>

        <div className="card up-card">
          <div className="up-card-head">
            <div className="ct">История обращений</div>
            <button type="button" className="up-btn sec" onClick={() => navigate("/call")}>
              Регистрация звонка
            </button>
          </div>
          {data.tickets.length === 0 ? (
            <p className="up-muted">Обращений не найдено</p>
          ) : (
            <table className="dt up-tickets">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тема</th>
                  <th>Категория</th>
                  <th>Линия</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {data.tickets.map((t) => (
                  <tr
                    key={t.id}
                    className="up-ticket-row"
                    onClick={() => navigate(`/tickets/${t.id}`)}
                  >
                    <td>{fmtDt(t.date_of_create)}</td>
                    <td>
                      <strong>{t.title}</strong>
                    </td>
                    <td>
                      {t.category ? (
                        <span
                          className={`ch-cat ch-cat--${categoryBadgeClass(t.category_theme, t.category)}`}
                          title={t.category}
                        >
                          {t.category}
                        </span>
                      ) : (
                        <span className="ch-cat ch-cat--empty">—</span>
                      )}
                    </td>
                    <td>
                      <span className={`ch-line ch-line--${supportLineBadgeClass(t.support_line)}`}>
                        {supportLineLabel(t.support_line, t.support_line_label)}
                      </span>
                    </td>
                    <td>
                      <span className={`ch-status ch-status--${t.status}`}>{t.status_label}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {modal ? (
        <div className="up-modal-back" onClick={() => !busy && setModal(null)}>
          <div className="up-modal" onClick={(e) => e.stopPropagation()}>
            {modal === "unfreeze" ? (
              <>
                <div className="up-modal-title">Разморозить тариф?</div>
                <p>Тариф будет восстановлен для абонента.</p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() => runAction(() => postUnfreeze(uid))}
                  >
                    Разморозить
                  </button>
                </div>
              </>
            ) : null}
            {modal === "unarchive" ? (
              <>
                <div className="up-modal-title">Восстановить УЗ?</div>
                <p>Вы точно хотите восстановить УЗ данного пользователя?</p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() => runAction(() => postUnarchive(uid))}
                  >
                    Восстановить
                  </button>
                </div>
              </>
            ) : null}
            {modal === "disconnect" ? (
              <>
                <div className="up-modal-title">Закрыть активные сессии?</div>
                <p>
                  Активных сессий: {data.open_sessions_count}. После подтверждения они закроются в течение
                  минуты.
                </p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() => runAction(() => postDisconnect(uid))}
                  >
                    Закрыть
                  </button>
                </div>
              </>
            ) : null}
            {modal === "freeze" ? (
              <>
                <div className="up-modal-title">Заморозка тарифа</div>
                <p className="up-muted">
                  Укажите дату заморозки. Пустое поле — заморозить сейчас. Будущая дата — только запись в
                  расписании.
                </p>
                <label className="up-label">
                  Дата заморозки
                  <input
                    type="datetime-local"
                    className="up-input"
                    value={freezeDate}
                    onChange={(e) => setFreezeDate(e.target.value)}
                  />
                </label>
                {!showUnfreezeDate ? (
                  <button type="button" className="up-link" onClick={() => setShowUnfreezeDate(true)}>
                    + Указать время разморозки
                  </button>
                ) : (
                  <label className="up-label">
                    Дата разморозки
                    <input
                      type="datetime-local"
                      className="up-input"
                      value={unfreezeDate}
                      onChange={(e) => setUnfreezeDate(e.target.value)}
                    />
                  </label>
                )}
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() =>
                      runAction(() =>
                        postFreeze(uid, {
                          date_freeze: freezeDate ? new Date(freezeDate).toISOString() : null,
                          date_unfreeze:
                            showUnfreezeDate && unfreezeDate
                              ? new Date(unfreezeDate).toISOString()
                              : null,
                        }),
                      )
                    }
                  >
                    Подтвердить
                  </button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
