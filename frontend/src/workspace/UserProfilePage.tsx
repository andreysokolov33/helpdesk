import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteFreezePlan,
  fetchUserProfile,
  fetchUserProfileTickets,
  postDisconnect,
  postFreeze,
  postRemoveEndedTariff,
  postUnarchive,
  postUnfreeze,
  type TariffBlockResponse,
  type ProfileTariff,
  type ProfileTicket,
  type UserProfileResponse,
} from "@/api/userProfile";
import { copyPhone, formatPhoneDisplay } from "@/utils/phone";
import { AuthPageHelp } from "@/components/AuthPageHelp";
import FastCheckPanel from "@/components/FastCheckPanel";
import PaymentsHistoryPanel from "@/components/PaymentsHistoryPanel";
import TariffsHistoryPanel from "@/components/TariffsHistoryPanel";
import DatePickerField, { dateYmdToIso } from "@/components/DatePickerField";
import { PasswordResetModal } from "@/components/PasswordResetModal";
import ToastNotice, { type ToastVariant } from "@/components/ToastNotice";
import { categoryBadgeClass, supportLineBadgeClass, supportLineLabel } from "@/utils/ticketLabels";

type ModalKind =
  | "unfreeze"
  | "unarchive"
  | "disconnect"
  | "freeze"
  | "cancel_planned_freeze"
  | "remove_ended_tariff"
  | "password_reset"
  | null;

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

function hasJurDopPacket(mb: number | null | undefined): boolean {
  return mb != null && mb > 0;
}

function statusClass(us: number | null) {
  if (us === 3) return "up-badge arch";
  if (us === 2) return "up-badge frz";
  return "up-badge ok";
}

function entityClass(isJuridical: number) {
  return isJuridical === 2 ? "up-badge jur" : "up-badge phys";
}

function splitEmails(email: string | null, isJuridical: number): string[] {
  if (!email?.trim()) return [];
  if (isJuridical !== 2) return [email.trim()];
  return email
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);
}

function EmailValue({ email, isJuridical }: { email: string | null; isJuridical: number }) {
  const list = splitEmails(email, isJuridical);
  if (list.length === 0) return <span className="up-v">—</span>;
  if (list.length === 1) return <span className="up-v">{list[0]}</span>;
  return (
    <span className="up-v up-email-list">
      {list.map((addr) => (
        <span key={addr} className="up-email-line">
          {addr}
        </span>
      ))}
    </span>
  );
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


function TariffSideColumn({ balance, authPage }: { balance: number; authPage: string | null }) {
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
    </div>
  );
}

function TariffCard({
  tariff,
  netflowNote,
  netflowTariff,
  isJuridical,
  onFreeze,
  onUnfreeze,
  onCancelPlan,
  onRemoveEndedTariff,
  openSessionsCount,
  onDisconnect,
}: {
  tariff: ProfileTariff | null;
  netflowNote: string | null;
  netflowTariff: string | null;
  isJuridical: number;
  openSessionsCount: number;
  onFreeze: () => void;
  onUnfreeze: () => void;
  onCancelPlan: () => void;
  onRemoveEndedTariff?: () => void;
  onDisconnect: () => void;
}) {
  if (!tariff && !netflowTariff) {
    return (
      <div className="card up-card up-tariff up-tariff-main">
        <div className="ct up-tariff-title">Тарифный план</div>
        <div className="up-tariff-empty" role="status">
          <div className="up-tariff-empty__title">Тариф не подключён</div>
          <p className="up-tariff-empty__text">
            Абоненту нужно выбрать подходящий тарифный план в личном кабинете на странице{" "}
            <strong>«Тариф»</strong>. Без подключённого тарифа доступ в интернет недоступен.
          </p>
        </div>
      </div>
    );
  }

  const isFrozen = tariff?.state === "frozen";
  const isPlannedFreeze = tariff?.state === "planned_freeze";
  const isTariffEnded = Boolean(tariff && !isFrozen && !isPlannedFreeze && !tariff.is_active);
  const canManageTariff = isJuridical === 0;
  const freezeLabel = tariff?.can_unfreeze
    ? "Разморозить"
    : isPlannedFreeze
      ? "Отменить заморозку"
      : "Заморозить";
  const freezeEnabled =
    canManageTariff &&
    Boolean(
      tariff?.can_unfreeze ||
        tariff?.can_freeze ||
        (isPlannedFreeze && tariff?.can_cancel_planned_freeze),
    );
  const freezeHandler = tariff?.can_unfreeze
    ? onUnfreeze
    : isPlannedFreeze
      ? onCancelPlan
      : onFreeze;
  const sessionsLabel =
    openSessionsCount > 0 ? `Закрыть сессии (${openSessionsCount})` : "Закрыть сессии";
  const showSessionsBtn = !isFrozen && tariff?.can_disconnect_sessions !== false;

  return (
    <div className="card up-card up-tariff up-tariff-main">
      <div className="up-tariff-head">
        <div className="ct up-tariff-title">Тарифный план</div>
      </div>

      {isTariffEnded ? (
        onRemoveEndedTariff ? (
          <button
            type="button"
            className="up-tariff-ended-banner up-tariff-ended-banner--action"
            onClick={onRemoveEndedTariff}
          >
            <span className="up-tariff-ended-banner__title">Тариф закончился</span>
            <span className="up-tariff-ended-banner__hint">Нажмите, чтобы отключить</span>
          </button>
        ) : (
          <div className="up-tariff-ended-banner" role="status">
            Тариф закончился
          </div>
        )
      ) : canManageTariff && !isFrozen ? (
        <div className="up-tariff-toolbar">
          <button
            type="button"
            className="up-tariff-btn up-tariff-btn--freeze"
            disabled={!freezeEnabled}
            onClick={freezeEnabled ? freezeHandler : undefined}
          >
            {freezeLabel}
          </button>
          {showSessionsBtn ? (
            <button type="button" className="up-tariff-btn up-tariff-btn--sessions" onClick={onDisconnect}>
              {sessionsLabel}
            </button>
          ) : (
            <span />
          )}
        </div>
      ) : null}

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

      {isFrozen && tariff ? (
        <>
          <div className="up-frozen-panel">
            <div className="up-frozen-title">Тариф заморожен</div>
            {tariff.frozen_at ? <div className="up-frozen-meta">Заморожен: {tariff.frozen_at}</div> : null}
            <hr className="up-frozen-divider" />
            <div className="up-frozen-unfreeze-row">
              Дата разморозки:{" "}
              {tariff.unfreeze_at ? (
                <strong>{tariff.unfreeze_at}</strong>
              ) : (
                <span className="up-frozen-unfreeze-missing">не установлена</span>
              )}
            </div>
            {canManageTariff && tariff.can_unfreeze ? (
              <button type="button" className="up-frozen-unfreeze-btn" onClick={onUnfreeze}>
                Разморозить тариф
              </button>
            ) : null}
          </div>

          <div className="up-kv">
            <span className="up-k">Название</span>
            <span className="up-v">{tariff.tariff_name}</span>
          </div>
          {isJuridical === 2 ? (
            <>
              {tariff.jur_main_packet_mb != null ? (
                <div className="up-kv">
                  <span className="up-k">Остаток основного пакета</span>
                  <span className="up-v up-frozen-traffic-val">
                    {fmtTrafficMb(tariff.jur_main_packet_mb)} МБ
                  </span>
                </div>
              ) : null}
              {tariff.overrun_mb != null && tariff.overrun_mb > 0 ? (
                <div className="up-kv">
                  <span className="up-k">Использовано доп. трафика</span>
                  <span className="up-v up-frozen-traffic-val">
                    {fmtTrafficMb(tariff.overrun_mb)} МБ
                  </span>
                </div>
              ) : null}
            </>
          ) : (
            <div className="up-kv up-frozen-traffic">
              <span className="up-k">Трафик (остаток / всего)</span>
              <span className="up-v up-frozen-traffic-val">
                {fmtTrafficMb(tariff.remain_traffic_mb)} / {fmtTrafficMb(tariff.full_packet_mb)} МБ
              </span>
            </div>
          )}
          {tariff.frozen_remaining_label ? (
            <div className="up-kv">
              <span className="up-k">Замороженный срок</span>
              <span className="up-v">{tariff.frozen_remaining_label}</span>
            </div>
          ) : null}

          <p className="up-frozen-footnote">
            * Действие услуг приостановлено. Пакеты трафика и сроки действия не расходуются.
          </p>
        </>
      ) : null}

      {tariff && !isFrozen ? (
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
            <span className="up-k">
              {tariff.speed_unlimited ? "Суточный трафик (остаток / лимит)" : "Трафик (остаток / всего)"}
            </span>
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
          {(isJuridical === 2 && !tariff.speed_unlimited) ||
          hasJurDopPacket(tariff.jur_dop_packet_mb) ? (
            <div className="up-kv">
              <span className="up-k">
                {hasJurDopPacket(tariff.jur_dop_packet_mb) ? "Доп. пакет (ЮЛ)" : "Доп. пакет"}
              </span>
              <span className="up-v">
                {hasJurDopPacket(tariff.jur_dop_packet_mb)
                  ? `${tariff.jur_dop_packet_mb!.toLocaleString("ru-RU")} МБ`
                  : "не предусмотрен"}
              </span>
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
  const [toast, setToast] = useState<{ message: string; variant: ToastVariant } | null>(null);
  const [ticketsPage, setTicketsPage] = useState(1);
  const [tickets, setTickets] = useState<ProfileTicket[]>([]);
  const [ticketsTotal, setTicketsTotal] = useState(0);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [ticketsErr, setTicketsErr] = useState<string | null>(null);
  const profileWrapRef = useRef<HTMLDivElement>(null);
  const [statsHeight, setStatsHeight] = useState<number | null>(null);

  const ticketsPerPage = 10;
  const ticketsTotalPages = Math.max(1, Math.ceil(ticketsTotal / ticketsPerPage));

  const reload = useCallback(() => {
    if (!Number.isFinite(uid)) return;
    setLoading(true);
    setTicketsLoading(true);
    setTicketsErr(null);
    setTicketsPage(1);
    fetchUserProfile(uid, 1, ticketsPerPage, false)
      .then((r) => {
        setData(r);
        setLoading(false);
        return fetchUserProfileTickets(uid, 1, ticketsPerPage).catch((e: unknown) => {
          setTicketsErr(e instanceof Error ? e.message : "Не удалось загрузить обращения");
          setTickets([]);
          setTicketsTotal(0);
          return null;
        });
      })
      .then((t) => {
        if (t) {
          setTickets(t.items);
          setTicketsTotal(t.total);
          setTicketsErr(null);
        }
      })
      .catch((e: unknown) => setErr(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => {
        setLoading(false);
        setTicketsLoading(false);
      });
  }, [uid, ticketsPerPage]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    const el = profileWrapRef.current;
    if (!el) return;

    const sync = () => {
      const h = el.getBoundingClientRect().height;
      if (h > 0) setStatsHeight(Math.round(h));
    };

    sync();
    const ro = new ResizeObserver(sync);
    ro.observe(el);
    window.addEventListener("resize", sync);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", sync);
    };
  }, [data, loading]);

  const loadTicketsPage = useCallback(
    (page: number) => {
      if (!Number.isFinite(uid)) return;
      setTicketsPage(page);
      setTicketsLoading(true);
      setTicketsErr(null);
      fetchUserProfileTickets(uid, page, ticketsPerPage)
        .then((r) => {
          setTickets(r.items);
          setTicketsTotal(r.total);
        })
        .catch((e: unknown) => {
          setTickets([]);
          setTicketsTotal(0);
          setTicketsErr(e instanceof Error ? e.message : "Не удалось загрузить обращения");
        })
        .finally(() => setTicketsLoading(false));
    },
    [uid, ticketsPerPage],
  );

  async function runAction(fn: () => Promise<{ message: string }>) {
    setBusy(true);
    try {
      const r = await fn();
      setToast({ message: r.message, variant: "success" });
      setModal(null);
      reload();
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Ошибка",
        variant: "error",
      });
    } finally {
      setBusy(false);
    }
  }

  async function runTariffBlockAction(fn: () => Promise<TariffBlockResponse>) {
    setBusy(true);
    try {
      const r = await fn();
      setToast({ message: r.message, variant: "success" });
      setModal(null);
      setData((prev) =>
        prev
          ? {
              ...prev,
              tariff: r.tariff,
              netflow_note: r.netflow_note,
              netflow_tariff: r.netflow_tariff,
              health_check: r.health_check,
            }
          : prev,
      );
    } catch (e: unknown) {
      setToast({
        message: e instanceof Error ? e.message : "Ошибка",
        variant: "error",
      });
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
              <span className="up-session-meta">последняя авторизация {data.online.last_session_end_label}</span>
            ) : null}
          </div>
        </div>

        <div className="up-stack">
        <div className="up-grid">
            <div ref={profileWrapRef} className="up-profile-wrap">
              <div className="card up-card up-personal">
                <div className="ct">Персональные данные</div>
                <div className="up-personal-details">
                  <div
                    className={`up-kv${p.is_juridical === 2 && splitEmails(p.email, p.is_juridical).length > 1 ? " up-kv--multiline" : ""}`}
                  >
                    <span className="up-k">Почта</span>
                    <EmailValue email={p.email} isJuridical={p.is_juridical} />
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
                </div>
              </div>
              <TariffCard
                tariff={data.tariff}
                netflowNote={data.netflow_note}
                netflowTariff={data.netflow_tariff}
                isJuridical={p.is_juridical}
                openSessionsCount={data.open_sessions_count}
                onFreeze={() => {
                  setFreezeDate("");
                  setUnfreezeDate("");
                  setShowUnfreezeDate(false);
                  setModal("freeze");
                }}
                onUnfreeze={() => setModal("unfreeze")}
                onCancelPlan={() => setModal("cancel_planned_freeze")}
                onRemoveEndedTariff={() => setModal("remove_ended_tariff")}
                onDisconnect={() => setModal("disconnect")}
              />
              <div className="up-aside-top">
                <div className="card up-card up-metric-cell up-personal-metric">
                  <div className="ct">ID</div>
                  <div className="up-metric-val up-personal-id-val">{p.user_id}</div>
                </div>
                <div className="card up-card up-metric-cell up-personal-metric">
                  <div className="ct">Логин</div>
                  <div className="up-metric-val up-personal-login-val" title={p.login || undefined}>
                    {p.login || "—"}
                  </div>
                </div>
              </div>
              <div className="up-aside-bottom">
                {p.user_status === 3 && p.is_juridical === 0 ? (
                  <button
                    type="button"
                    className="up-btn up-btn-restore up-reset-pwd"
                    onClick={() => setModal("unarchive")}
                  >
                    Восстановить УЗ
                  </button>
                ) : p.user_status !== 3 ? (
                  <button
                    type="button"
                    className="up-btn sec up-reset-pwd"
                    onClick={() => setModal("password_reset")}
                  >
                    Сменить пароль
                  </button>
                ) : null}
                <TariffSideColumn balance={data.balance} authPage={p.auth_page} />
              </div>
            </div>
            <div
              className="card up-card up-stats"
              style={statsHeight ? { height: statsHeight, maxHeight: statsHeight } : undefined}
            >
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
                  <FastCheckPanel
                    userId={p.user_id}
                    onDisconnect={() => postDisconnect(p.user_id).then(() => reload())}
                  />
                ) : report === "payments" ? (
                  <PaymentsHistoryPanel userId={p.user_id} />
                ) : report === "tariffs" ? (
                  <TariffsHistoryPanel userId={p.user_id} />
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
          {ticketsLoading ? (
            <p className="up-muted">Загрузка…</p>
          ) : ticketsErr ? (
            <p className="up-muted up-error">{ticketsErr}</p>
          ) : ticketsTotal === 0 ? (
            <div className="up-tickets-empty" role="status">
              <div className="up-tickets-empty__title">Обращений пока не было</div>
              <p className="up-tickets-empty__text">
                У этого абонента ещё не создавались обращения в техническую поддержку. Новое
                обращение можно зарегистрировать по кнопке «Регистрация звонка» выше.
              </p>
            </div>
          ) : (
            <>
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
                  {tickets.map((t) => (
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
              {ticketsTotal > ticketsPerPage ? (
                <div className="ch-pager">
                  <button
                    type="button"
                    className="ch-page-btn"
                    disabled={ticketsPage <= 1 || ticketsLoading}
                    onClick={() => loadTicketsPage(Math.max(1, ticketsPage - 1))}
                  >
                    Назад
                  </button>
                  <span className="ch-page-info">
                    Стр. {ticketsPage} / {ticketsTotalPages} · всего {ticketsTotal}
                  </span>
                  <button
                    type="button"
                    className="ch-page-btn"
                    disabled={ticketsPage >= ticketsTotalPages || ticketsLoading}
                    onClick={() => loadTicketsPage(ticketsPage + 1)}
                  >
                    Вперёд
                  </button>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      {modal ? (
        <div className="up-modal-back" onClick={() => !busy && setModal(null)}>
          {modal === "password_reset" ? (
            <PasswordResetModal
              userId={uid}
              busy={busy}
              setBusy={setBusy}
              onClose={() => setModal(null)}
              onError={(msg) => setToast({ message: msg, variant: "error" })}
            />
          ) : (
          <div
            className={`up-modal${modal === "freeze" ? " up-modal--freeze" : ""}`}
            onClick={(e) => e.stopPropagation()}
          >
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
                    Разморозить тариф
                  </button>
                </div>
              </>
            ) : null}
            {modal === "cancel_planned_freeze" ? (
              <>
                <div className="up-modal-title">Отменить заморозку?</div>
                <p>Запланированная заморозка тарифа будет удалена из расписания.</p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Нет
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() => runAction(() => deleteFreezePlan(uid))}
                  >
                    Да, отменить
                  </button>
                </div>
              </>
            ) : null}
            {modal === "remove_ended_tariff" ? (
              <>
                <div className="up-modal-title">Отключить тариф?</div>
                <p className="up-modal-lead">
                  У абонента <strong>истёк срок действия тарифа</strong> — интернет по этому тарифу недоступен.
                </p>
                <p>
                  Если абонент не может сам отключить тариф в личном кабинете (вкладка{" "}
                  <strong>«Тарифы»</strong>), вы можете сделать это здесь. После подтверждения тариф будет снят
                  с учётной записи.
                </p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" disabled={busy} onClick={() => setModal(null)}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="up-btn pri"
                    disabled={busy}
                    onClick={() => runTariffBlockAction(() => postRemoveEndedTariff(uid))}
                  >
                    Отключить тариф
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
                    className="up-btn up-btn-restore"
                    disabled={busy}
                    onClick={() => runAction(() => postUnarchive(uid))}
                  >
                    Да
                  </button>
                </div>
              </>
            ) : null}
            {modal === "disconnect" ? (
              data.open_sessions_count > 0 ? (
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
              ) : (
                <>
                  <div className="up-modal-title">Закрыть сессии</div>
                  <p>Активных сессий на данной УЗ нет.</p>
                  <div className="up-modal-actions">
                    <button type="button" className="up-btn sec" onClick={() => setModal(null)}>
                      Понятно
                    </button>
                  </div>
                </>
              )
            ) : null}
            {modal === "freeze" ? (
              <>
                <div className="up-modal-title">Заморозка тарифа</div>
                <div className="up-freeze-modal-hints">
                  <p>
                    Если поле <strong>«Дата заморозки»</strong> оставить пустым и нажать{" "}
                    <strong>«Подтвердить»</strong>, тариф будет <strong>заморожен сразу</strong> — абонент
                    потеряет доступ к услуге в течение минуты.
                  </p>
                  <p>
                    Если указать <strong>дату в будущем</strong>, заморозка только запишется в
                    расписание: до наступления этой даты тариф останется активным.
                  </p>
                  <p className="up-freeze-modal-hints-note">
                    Дату разморозки можно добавить по желанию — иначе абонент разморозит тариф самостоятельно
                    или через оператора.
                  </p>
                </div>
                <div className="up-freeze-dt-block">
                  <div className="up-freeze-dt-head">
                    <span className="up-label up-label--inline">Дата заморозки</span>
                    {freezeDate ? (
                      <button
                        type="button"
                        className="up-link up-link--inline"
                        onClick={() => setFreezeDate("")}
                      >
                        Очистить
                      </button>
                    ) : null}
                  </div>
                  <span className="up-label-hint">необязательно — пустое поле = заморозка сейчас</span>
                  <DatePickerField
                    value={freezeDate}
                    onChange={setFreezeDate}
                    id="freeze-date"
                    placeholder="Не выбрано — заморозка сейчас"
                  />
                </div>
                {!showUnfreezeDate ? (
                  <button type="button" className="up-link" onClick={() => setShowUnfreezeDate(true)}>
                    + Указать дату разморозки
                  </button>
                ) : (
                  <div className="up-freeze-dt-block">
                    <div className="up-freeze-dt-head">
                      <span className="up-label up-label--inline">Дата разморозки</span>
                      {unfreezeDate ? (
                        <button
                          type="button"
                          className="up-link up-link--inline"
                          onClick={() => setUnfreezeDate("")}
                        >
                          Очистить
                        </button>
                      ) : null}
                    </div>
                    <DatePickerField
                      value={unfreezeDate}
                      onChange={setUnfreezeDate}
                      minDate={freezeDate || undefined}
                      id="unfreeze-date"
                      placeholder="Выберите дату"
                    />
                  </div>
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
                          date_freeze: freezeDate ? dateYmdToIso(freezeDate) : null,
                          date_unfreeze:
                            showUnfreezeDate && unfreezeDate ? dateYmdToIso(unfreezeDate) : null,
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
          )}
        </div>
      ) : null}

      {toast ? (
        <ToastNotice
          message={toast.message}
          variant={toast.variant}
          onClose={() => setToast(null)}
        />
      ) : null}
    </div>
  );
}
