import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteFreezePlan,
  fetchUserProfile,
  postDisconnect,
  postFreeze,
  postRemoveEndedTariff,
  postUnarchive,
  postUnfreeze,
  type ProfilePersonal,
  type TariffBlockResponse,
  type ProfileTariff,
  type UserProfileResponse,
} from "@/api/userProfile";
import type { SubscriberSearchHit } from "@/api/search";
import { copyPhone, formatPhoneDisplay } from "@/utils/phone";
import { AuthPageHelp } from "@/components/AuthPageHelp";
import FastCheckPanel from "@/components/FastCheckPanel";
import PaymentsHistoryPanel from "@/components/PaymentsHistoryPanel";
import TariffsHistoryPanel from "@/components/TariffsHistoryPanel";
import TicketsHistoryPanel from "@/components/TicketsHistoryPanel";
import OpenSessionsCard from "@/components/OpenSessionsCard";
import DatePickerField, { dateYmdToIso } from "@/components/DatePickerField";
import { PasswordResetModal } from "@/components/PasswordResetModal";
import ToastNotice, { type ToastVariant } from "@/components/ToastNotice";

type StatsTab = "payments" | "tariffs" | "appeals";

const STATS_TABS: { id: StatsTab; label: string }[] = [
  { id: "payments", label: "История платежей" },
  { id: "tariffs", label: "История тарифов" },
  { id: "appeals", label: "Обращения" },
];

type ModalKind =
  | "unfreeze"
  | "unfreeze_blocked"
  | "unarchive"
  | "disconnect"
  | "freeze"
  | "freeze_blocked"
  | "cancel_planned_freeze"
  | "remove_ended_tariff"
  | "password_reset"
  | null;

function fmtMoney(n: number) {
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₽`;
}

function fmtTrafficMb(n: number) {
  return n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

function hasJurDopPacket(mb: number | null | undefined): boolean {
  return mb != null && mb > 0;
}

function JurDopOverrunBlock({
  overrunMb,
  dopPacketMb,
}: {
  overrunMb: number;
  dopPacketMb: number | null | undefined;
}) {
  return (
    <div className="up-jur-overrun" role="status">
      <div className="up-jur-overrun__icon" aria-hidden>
        ↗
      </div>
      <div className="up-jur-overrun__body">
        <div className="up-jur-overrun__title">Перерасход трафика</div>
        <p className="up-jur-overrun__main">
          <span className="up-jur-overrun__value">{fmtTrafficMb(overrunMb)} МБ</span>
          {hasJurDopPacket(dopPacketMb) ? (
            <>
              {" из "}
              <span className="up-jur-overrun__source">
                {dopPacketMb!.toLocaleString("ru-RU")} МБ
              </span>
            </>
          ) : null}
        </p>
      </div>
    </div>
  );
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

function PassportSpoiler({ passport }: { passport: string | null }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="up-pass-spoiler">
      <button type="button" className="up-pass-btn" onClick={() => setOpen((v) => !v)}>
        {open ? "Скрыть" : "Показать паспортные данные"}
      </button>
      {open ? <div className="up-pass-data">{passport ?? "—"}</div> : null}
    </div>
  );
}


function profileToSearchHit(p: ProfilePersonal): SubscriberSearchHit {
  return {
    id: p.user_id,
    login: p.login,
    name: p.name,
    email: p.email,
    phone: p.phone,
    id_doc: p.id_doc,
    is_juridical: p.is_juridical,
  };
}

function canShowOpenSessions(
  userStatus: number | null,
  tariff: ProfileTariff | null,
  netflowTariff: string | null,
): boolean {
  if (userStatus === 3 || userStatus === 2) return false;
  if (!tariff && !netflowTariff) return false;
  if (tariff?.state === "frozen" || tariff?.state === "planned_freeze") return false;
  return true;
}

function balanceTone(balance: number): "ok" | "warn" | "bad" {
  if (balance <= 0) return "bad";
  if (balance < 1000) return "warn";
  return "ok";
}

function ProfileMetricStrip({
  userId,
  login,
  balance,
  authPage,
  stationName,
}: {
  userId: number;
  login: string;
  balance: number;
  authPage: string | null;
  stationName: string | null;
}) {
  const balanceClass = balanceTone(balance);
  return (
    <div className="card up-card up-metric-strip">
      <div className="up-metric-strip__cell">
        <span className="up-metric-strip__lbl">ID</span>
        <span className="up-metric-strip__val">{userId}</span>
      </div>
      <div className="up-metric-strip__cell">
        <span className="up-metric-strip__lbl">Логин</span>
        <span className="up-metric-strip__val up-metric-strip__val--login" title={login || undefined}>
          {login || "—"}
        </span>
      </div>
      <div className="up-metric-strip__cell">
        <span className="up-metric-strip__lbl">Баланс</span>
        <span className={`up-metric-strip__val up-metric-strip__val--balance ${balanceClass}`}>
          {fmtMoney(balance)}
        </span>
      </div>
      <div className="up-metric-strip__cell">
        <span className="up-metric-strip__lbl up-metric-strip__lbl--auth">
          Страница авторизации
          <AuthPageHelp hotspotAddress={authPage} />
        </span>
        <span className="up-metric-strip__val up-metric-strip__val--mono">{authPage ?? "—"}</span>
      </div>
      <div className="up-metric-strip__cell">
        <span className="up-metric-strip__lbl">Станция</span>
        <span className="up-metric-strip__val">{stationName ?? "—"}</span>
      </div>
    </div>
  );
}

function TariffCard({
  tariff,
  netflowNote,
  netflowTariff,
  isJuridical,
  userStatus,
  onFreeze,
  onUnfreeze,
  onCancelPlan,
  onRemoveEndedTariff,
  openSessionsCount,
  disconnectSessionsRemaining,
  disconnectSessionsLimit,
  disconnectSessionsWindowMinutes,
  onDisconnect,
}: {
  tariff: ProfileTariff | null;
  netflowNote: string | null;
  netflowTariff: string | null;
  isJuridical: number;
  userStatus: number | null;
  openSessionsCount: number;
  disconnectSessionsRemaining: number;
  disconnectSessionsLimit: number;
  disconnectSessionsWindowMinutes: number;
  onFreeze: () => void;
  onUnfreeze: () => void;
  onCancelPlan: () => void;
  onRemoveEndedTariff?: () => void;
  onDisconnect: () => void;
}) {
  if (userStatus === 3) {
    return (
      <div className="card up-card up-tariff up-tariff-main">
        <div className="ct up-tariff-title">Тарифный план</div>
        <div className="up-tariff-empty up-tariff-empty--archived" role="status">
          <div className="up-tariff-empty__title">Учётная запись абонента архивирована</div>
          <p className="up-tariff-empty__text">
            Он не может ни войти в личный кабинет, ни работать в нашей сети. Если он хочет продолжить
            пользоваться этой учётной записью, восстановите УЗ.
          </p>
        </div>
      </div>
    );
  }

  if (!tariff && !netflowTariff) {
    return (
      <div className="card up-card up-tariff up-tariff-main">
        <div className="ct up-tariff-title">Тарифный план</div>
        <div className="up-tariff-empty" role="status">
          <div className="up-tariff-empty__title">Тариф не подключен</div>
          <p className="up-tariff-empty__text">
            Абоненту нужно выбрать подходящий тарифный план в личном кабинете на странице{" "}
            <strong>«Тариф»</strong>. Без подключенного тарифа доступ в интернет недоступен.
          </p>
        </div>
      </div>
    );
  }

  const isFrozen = tariff?.state === "frozen";
  const isPlannedFreeze = tariff?.state === "planned_freeze";
  const isTariffEnded = Boolean(tariff && !isFrozen && !isPlannedFreeze && !tariff.is_active);
  const isJur = isJuridical === 2;
  const canManageTariff = !isJur;
  const canRemoveEnded = canManageTariff && Boolean(tariff?.can_remove_ended_tariff);
  const freezeLabel = tariff?.can_unfreeze
    ? "Разморозить"
    : isPlannedFreeze
      ? "Отменить заморозку"
      : "Заморозить";
  const freezeEnabled =
    canManageTariff &&
    Boolean(
      tariff?.can_unfreeze ||
        tariff?.unfreeze_blocked_message ||
        tariff?.can_freeze ||
        tariff?.freeze_blocked_message ||
        (isPlannedFreeze && tariff?.can_cancel_planned_freeze),
    );
  const freezeHandler = tariff?.can_unfreeze
    ? onUnfreeze
    : isPlannedFreeze
      ? onCancelPlan
      : onFreeze;
  const sessionsLabel =
    openSessionsCount > 0 ? `Закрыть сессии (${openSessionsCount})` : "Закрыть сессии";
  const sessionsAllowed =
    tariff?.can_disconnect_sessions !== false && disconnectSessionsRemaining > 0;
  const showSessionsBtn = sessionsAllowed && (!isFrozen || isJur);
  const sessionsLimitMsg = `Лимит сброса сессий исчерпан (${disconnectSessionsLimit} раза за ${disconnectSessionsWindowMinutes} мин.)`;
  const sessionsBtnTitle = disconnectSessionsRemaining <= 0 ? sessionsLimitMsg : undefined;
  const showFreezeBtn = canManageTariff && !isFrozen;
  const showToolbar = showFreezeBtn || (isJur && showSessionsBtn);
  const sessionsOnlyToolbar = isJur && showSessionsBtn && !showFreezeBtn;

  return (
    <div className="card up-card up-tariff up-tariff-main">
      <div className="up-tariff-head">
        <div className="ct up-tariff-title">Тарифный план</div>
      </div>

      {isTariffEnded ? (
        canRemoveEnded && onRemoveEndedTariff ? (
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
      ) : null}
      {showToolbar ? (
        <div
          className={
            sessionsOnlyToolbar
              ? "up-tariff-toolbar up-tariff-toolbar--sessions-only"
              : "up-tariff-toolbar"
          }
        >
          {showFreezeBtn ? (
            <button
              type="button"
              className="up-tariff-btn up-tariff-btn--freeze"
              disabled={!freezeEnabled}
              onClick={freezeEnabled ? freezeHandler : undefined}
            >
              {freezeLabel}
            </button>
          ) : null}
          {showSessionsBtn ? (
            <button
              type="button"
              className="up-tariff-btn up-tariff-btn--sessions"
              title={sessionsBtnTitle}
              onClick={onDisconnect}
            >
              {sessionsLabel}
            </button>
          ) : null}
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
            {canManageTariff && (tariff.can_unfreeze || tariff.unfreeze_blocked_message) ? (
              <button type="button" className="up-frozen-unfreeze-btn" onClick={onUnfreeze}>
                Разморозить тариф
              </button>
            ) : null}
            {isJur && showSessionsBtn ? (
              <button
                type="button"
                className="up-frozen-unfreeze-btn up-tariff-btn--sessions"
                title={sessionsBtnTitle}
                onClick={onDisconnect}
              >
                {sessionsLabel}
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
                <JurDopOverrunBlock
                  overrunMb={tariff.overrun_mb}
                  dopPacketMb={tariff.jur_dop_packet_mb}
                />
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
            isJuridical === 2 ? (
              <JurDopOverrunBlock
                overrunMb={tariff.overrun_mb}
                dopPacketMb={tariff.jur_dop_packet_mb}
              />
            ) : (
              <div className="up-alert bad">
                Перерасход трафика: ~{tariff.overrun_mb.toFixed(1)} МБ
              </div>
            )
          ) : null}
          {tariff.speed_unlimited && tariff.msk_reset ? (
            <>
              <div className="up-kv up-kv--multiline">
                <span className="up-k">Сброс суточного трафика</span>
                <span className="up-v up-v-col">
                  <span className="up-v-main">{tariff.msk_reset}</span>
                  {tariff.last_traffic_reset_label ? (
                    <span className="up-kv-sub">
                      Последний сброс: {tariff.last_traffic_reset_label}
                    </span>
                  ) : null}
                </span>
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
  const [statsTab, setStatsTab] = useState<StatsTab>("payments");
  const [modal, setModal] = useState<ModalKind>(null);
  const [freezeDate, setFreezeDate] = useState("");
  const [unfreezeDate, setUnfreezeDate] = useState("");
  const [showUnfreezeDate, setShowUnfreezeDate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<{ message: string; variant: ToastVariant } | null>(null);
  const reload = useCallback(() => {
    if (!Number.isFinite(uid)) return;
    setLoading(true);
    fetchUserProfile(uid, 1, 10, false)
      .then((r) => {
        setData(r);
        setErr(null);
      })
      .catch((e: unknown) => setErr(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setLoading(false));
  }, [uid]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    if (!Number.isFinite(uid)) return;
    const prev = document.title;
    document.title = `Профиль ${uid}`;
    return () => {
      document.title = prev;
    };
  }, [uid]);

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
  const showOpenSessions = canShowOpenSessions(p.user_status, data.tariff, data.netflow_tariff);

  return (
    <div className="tp on up-page">
      <div className="pg">
        <div className="up-top">
          <Link to="/" className="up-back">
            ← Поиск
          </Link>
          <div className="up-top-head">
            <h1 className="up-title">{p.name}</h1>
            <button
              type="button"
              className="up-btn sec up-call-register"
              onClick={() =>
                navigate("/call", {
                  state: {
                    returnTo: `/users/${uid}`,
                    prefillSubscriber: profileToSearchHit(p),
                  },
                })
              }
            >
              Регистрация звонка
            </button>
          </div>
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

        <ProfileMetricStrip
          userId={p.user_id}
          login={p.login}
          balance={data.balance}
          authPage={p.auth_page}
          stationName={p.station_name}
        />

        <div className="up-stack">
        <div className="up-grid">
            <div className="up-profile-wrap">
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
                  <div className="up-kv up-kv--multiline">
                    <span className="up-k">Адрес</span>
                    <span className="up-v">{p.residence_address ?? "—"}</span>
                  </div>
                  {p.is_juridical === 2 ? (
                    <div className="up-kv">
                      <span className="up-k">{idDocLabel}</span>
                      <span className="up-v">{p.id_doc ?? "—"}</span>
                    </div>
                  ) : (
                    <PassportSpoiler passport={p.id_doc} />
                  )}
                  {p.is_juridical === 2 ? (
                    <div className="up-kv">
                      <span className="up-k">Договор</span>
                      <span
                        className={
                          p.active_contract === "Не удалось найти договор" ? "up-v bad" : "up-v"
                        }
                      >
                        {p.active_contract ?? "—"}
                      </span>
                    </div>
                  ) : null}
                </div>
                <div className="up-personal-actions">
                  {p.user_status !== 3 ? (
                    <button
                      type="button"
                      className="up-btn sec up-reset-pwd"
                      onClick={() => setModal("password_reset")}
                    >
                      Сменить пароль
                    </button>
                  ) : null}
                </div>
              </div>
              <TariffCard
                tariff={data.tariff}
                netflowNote={data.netflow_note}
                netflowTariff={data.netflow_tariff}
                isJuridical={p.is_juridical}
                userStatus={p.user_status}
                openSessionsCount={data.open_sessions_count}
                disconnectSessionsRemaining={data.disconnect_sessions_remaining}
                disconnectSessionsLimit={data.disconnect_sessions_limit}
                disconnectSessionsWindowMinutes={data.disconnect_sessions_window_minutes}
                onFreeze={() => {
                  if (data.tariff?.freeze_blocked_message) {
                    setModal("freeze_blocked");
                    return;
                  }
                  setFreezeDate("");
                  setUnfreezeDate("");
                  setShowUnfreezeDate(false);
                  setModal("freeze");
                }}
                onUnfreeze={() => {
                  if (data.tariff?.unfreeze_blocked_message) {
                    setModal("unfreeze_blocked");
                    return;
                  }
                  setModal("unfreeze");
                }}
                onCancelPlan={() => setModal("cancel_planned_freeze")}
                onRemoveEndedTariff={() => setModal("remove_ended_tariff")}
                onDisconnect={() => {
                  if (data.disconnect_sessions_remaining <= 0) {
                    setToast({
                      message: `Лимит сброса сессий исчерпан (${data.disconnect_sessions_limit} раза за ${data.disconnect_sessions_window_minutes} мин.). Повторите позже.`,
                      variant: "error",
                    });
                    return;
                  }
                  setModal("disconnect");
                }}
              />
              {showOpenSessions ? <OpenSessionsCard sessions={data.open_sessions} /> : null}
            </div>
            <div className="up-right-col">
              <div className="card up-card up-diag-card">
                <div className="ct">Диагностика</div>
                <FastCheckPanel
                  userId={p.user_id}
                  introText="Запустите автоматическую проверку УЗ абонента — система проверит все параметры подключения и предложит алгоритм действий."
                  runButtonLabel="Запустить диагностику"
                  onDisconnect={() => postDisconnect(p.user_id).then(() => reload())}
                  onUnarchive={
                    p.user_status === 3 && p.is_juridical === 0
                      ? () => setModal("unarchive")
                      : undefined
                  }
                />
              </div>
              <div className="card up-card up-stats-card">
                <div className="ct">Статистика последних действий</div>
                <div className="up-stats-tabs" role="tablist" aria-label="Статистика последних действий абонента">
                  {STATS_TABS.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      role="tab"
                      aria-selected={statsTab === tab.id}
                      className={`up-stats-tab${statsTab === tab.id ? " active" : ""}`}
                      onClick={() => setStatsTab(tab.id)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                <div className="up-stats-pane">
                  {statsTab === "payments" ? (
                    <PaymentsHistoryPanel userId={p.user_id} />
                  ) : statsTab === "tariffs" ? (
                    <TariffsHistoryPanel userId={p.user_id} />
                  ) : (
                    <TicketsHistoryPanel userId={p.user_id} />
                  )}
                </div>
              </div>
            </div>
        </div>
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
            {modal === "unfreeze_blocked" ? (
              <>
                <div className="up-modal-title">Разморозка недоступна</div>
                <p className="up-modal-lead">
                  {data.tariff?.unfreeze_blocked_message ??
                    "Данный абонент был заморожен по техническим причинам. Создайте заявку инженерам, чтобы получить детали заморозки и примерные сроки разморозки тарифа абонента"}
                </p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" onClick={() => setModal(null)}>
                    Понятно
                  </button>
                </div>
              </>
            ) : null}
            {modal === "freeze_blocked" ? (
              <>
                <div className="up-modal-title">Заморозка недоступна</div>
                <p className="up-modal-lead">
                  {data.tariff?.freeze_blocked_message ??
                    "В рамках данного тарифа абоненту уже был заморожен тарифный план. Если абоненту требуется повторная заморозка, создайте тикет инженерам и опишите ситуацию, чтобы они приняли решение о повторной заморозке."}
                </p>
                <div className="up-modal-actions">
                  <button type="button" className="up-btn sec" onClick={() => setModal(null)}>
                    Понятно
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
                  <p className="up-muted">
                    Осталось попыток сброса за {data.disconnect_sessions_window_minutes} мин.:{" "}
                    {data.disconnect_sessions_remaining} из {data.disconnect_sessions_limit}.
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
