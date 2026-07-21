import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { TicketDetail, TicketPriority } from "@/api/ticket";
import type { FastCheckResponse, UserProfileResponse } from "@/api/userProfile";
import FastCheckPanel from "@/components/FastCheckPanel";
import TicketKbSearch from "@/components/TicketKbSearch";
import TicketStaffParticipants from "@/components/TicketStaffParticipants";
import TopSubscriberBadge from "@/components/TopSubscriberBadge";
import { formatDateTimeLocal } from "@/utils/dateTime";
import { ticketListStatusColumn } from "@/api/tracker";
import { formatWorkDurationSince } from "@/utils/ticketFormat";
import {
  priorityBadgeClass,
  queueLineBadgeClass,
  queueLineShortLabel,
} from "@/utils/ticketLabels";

const PRIORITY_OPTIONS: { id: TicketPriority; label: string }[] = [
  { id: "low", label: "Низкий" },
  { id: "middle", label: "Средний" },
  { id: "high", label: "Высокий" },
  { id: "critical", label: "Критический" },
];

function priorityLabel(priority: string | null | undefined): string {
  const id = (priority as TicketPriority) || "middle";
  return PRIORITY_OPTIONS.find((o) => o.id === id)?.label ?? "Средний";
}

function fmtMoney(n: number) {
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₽`;
}

type Props = {
  detail: TicketDetail;
  profile: UserProfileResponse | null;
  collapsed: boolean;
  onToggle: () => void;
  nowPulse: number;
  checkCache: FastCheckResponse | null;
  onCheckCache: (data: FastCheckResponse) => void;
  onDisconnect: () => void;
  transferLoading: boolean;
  takeBackLoading: boolean;
  reopenLoading: boolean;
  priorityLoading: boolean;
  onTransfer: () => void;
  onTakeBack: () => void;
  onReopen: () => void;
  onChangePriority: (priority: TicketPriority) => void;
  onLinkSubscriber: () => void;
  onOpenKbArticle: (slug: string) => void;
  kbArticleOpen?: boolean;
  onMobileClose?: () => void;
};

export default function TicketHelperPanel({
  detail,
  profile,
  collapsed,
  onToggle,
  nowPulse,
  checkCache,
  onCheckCache,
  onDisconnect,
  transferLoading,
  takeBackLoading,
  reopenLoading,
  priorityLoading,
  onTransfer,
  onTakeBack,
  onReopen,
  onChangePriority,
  onLinkSubscriber,
  onOpenKbArticle,
  kbArticleOpen = false,
  onMobileClose,
}: Props) {
  const [diagOpen, setDiagOpen] = useState(false);
  const [runNonce, setRunNonce] = useState(0);
  const [checkLoading, setCheckLoading] = useState(false);
  const prioritySizerRef = useRef<HTMLSpanElement>(null);
  const [priorityWidth, setPriorityWidth] = useState<number | undefined>(undefined);
  const currentPriority = (detail.priority as TicketPriority) || "middle";
  const currentPriorityLabel = priorityLabel(detail.priority);
  const priorityMod = priorityBadgeClass(detail.priority);

  useLayoutEffect(() => {
    const el = prioritySizerRef.current;
    if (!el) return;
    const w = Math.ceil(el.getBoundingClientRect().width);
    setPriorityWidth(w > 0 ? w : undefined);
  }, [currentPriorityLabel, priorityMod]);

  useEffect(() => {
    setDiagOpen(false);
    setRunNonce(0);
    setCheckLoading(false);
  }, [detail.id]);

  function handleDiagnosticsClick() {
    if (!detail.user_id) return;
    if (diagOpen) {
      setDiagOpen(false);
      return;
    }
    setDiagOpen(true);
    setRunNonce((n) => n + 1);
  }
  const subscriberName =
    detail.subscriber_name?.trim() || detail.caller_name?.trim() || "Абонент";
  const online = Boolean(detail.user_id) && Boolean(detail.subscriber_online);
  const balance = detail.subscriber_account?.balance;
  const station = detail.station_name || profile?.personal.station_name || "—";
  const sessionIp =
    (online && profile?.open_sessions?.[0]?.ip_address) ||
    profile?.personal.auth_page ||
    "—";
  const workSince = detail.assigned_at_iso || detail.date_of_create_iso;
  const statusColumn = ticketListStatusColumn(detail);
  const reopenLabel = (() => {
    if (!detail.was_reopened) return null;
    const count = detail.reopen_count ?? 0;
    const when = formatDateTimeLocal(detail.last_reopened_at_iso);
    const timesWord = (n: number) => {
      const mod100 = n % 100;
      const mod10 = n % 10;
      if (mod10 === 1 && mod100 !== 11) return `${n} раз`;
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} раза`;
      return `${n} раз`;
    };
    if (count > 1 && when) return `${timesWord(count)} · ${when}`;
    if (count > 1) return timesWord(count);
    return when || "да";
  })();

  return (
    <div className="tk-cc-helper-wrap">
      <section
        className={`tk-cc-helper${collapsed ? " tk-cc-helper--collapsed" : ""}`}
        aria-label="Данные абонента и тикета"
      >
        {onMobileClose ? (
          <div className="tk-cc-mobile-drawer-head">
            <span>Абонент и тикет</span>
            <button type="button" className="tk-cc-drawer-close" onClick={onMobileClose} aria-label="Закрыть">
              ×
            </button>
          </div>
        ) : null}
        <div className="tk-cc-helper__section">
          <div className="tk-cc-helper__section-title">Данные активного абонента</div>
          {detail.user_id == null ? (
            <div className="tk-cc-sub-unknown">
              <p>Не удалось определить абонента</p>
              {detail.caller_name ? (
                <p className="tk-cc-sub-unknown__meta">Как представился: {detail.caller_name}</p>
              ) : null}
              <button type="button" className="tk-cc-btn tk-cc-btn--outline" onClick={onLinkSubscriber}>
                Найти абонента
              </button>
            </div>
          ) : (
            <>
              <div className="tk-cc-sub-head">
                {detail.subscriber_profile_user_id != null ? (
                  <Link
                    to={`/users/${detail.subscriber_profile_user_id}`}
                    className="tk-cc-sub-name"
                  >
                    {subscriberName}
                  </Link>
                ) : (
                  <span className="tk-cc-sub-name">{subscriberName}</span>
                )}
                <div className="tk-cc-sub-meta">
                  <span
                    className={`tk-cc-entity ${
                      detail.subscriber_is_juridical === 2 ? "tk-cc-entity--jur" : "tk-cc-entity--phys"
                    }`}
                  >
                    {detail.subscriber_is_juridical === 2 ? "Юр. лицо" : "Физ. лицо"}
                  </span>
                  <TopSubscriberBadge rank={detail.top_subscriber_rank} labeled />
                </div>
              </div>
              <div className="tk-cc-data-grid">
                <div className="tk-cc-data-cell">
                  <div className="tk-cc-data-cell__label">ID учётной записи</div>
                  <div className="tk-cc-data-cell__value">#{detail.user_id}</div>
                </div>
                <div className="tk-cc-data-cell">
                  <div className="tk-cc-data-cell__label">Баланс счёта</div>
                  <div className="tk-cc-data-cell__value">
                    {balance != null ? fmtMoney(balance) : "—"}
                  </div>
                </div>
                <div className="tk-cc-data-cell">
                  <div className="tk-cc-data-cell__label">Базовая станция</div>
                  <div className="tk-cc-data-cell__value">{station}</div>
                </div>
                <div className="tk-cc-data-cell">
                  <div className="tk-cc-data-cell__label">IP хотспота</div>
                  <div className="tk-cc-data-cell__value">{sessionIp}</div>
                </div>
              </div>
            </>
          )}

          <div
            className={`tk-cc-actions${
              !detail.is_open && !detail.can_reopen && detail.queue_line !== "engineers"
                ? " tk-cc-actions--single"
                : ""
            }`}
          >
            <button
              type="button"
              className={`tk-cc-btn tk-cc-btn--accent${checkLoading ? " tk-cc-btn--busy" : ""}${diagOpen ? " tk-cc-btn--active" : ""}`}
              onClick={handleDiagnosticsClick}
              disabled={!detail.user_id}
              title={detail.user_id ? "Быстрая проверка абонента" : "Укажите абонента в тикете"}
            >
              {checkLoading ? "Проверяю…" : "Диагностика"}
            </button>
            {detail.is_open && detail.queue_line === "cs" && detail.support_line !== 4 ? (
              <button
                type="button"
                className="tk-cc-btn tk-cc-btn--transfer"
                disabled={transferLoading}
                onClick={onTransfer}
                data-tip="Перевести тикет в зону ответственности инженеров"
              >
                {transferLoading ? "Передаю…" : "Передать инженерам"}
              </button>
            ) : detail.is_open && detail.queue_line === "engineers" ? (
              <button
                type="button"
                className="tk-cc-btn tk-cc-btn--takeback"
                disabled={takeBackLoading}
                onClick={onTakeBack}
                data-tip="Перевести тикет в зону ответственности первой линии техподдержки"
              >
                {takeBackLoading ? "Возврат…" : "Взять в работу"}
              </button>
            ) : detail.can_reopen ? (
              <button
                type="button"
                className="tk-cc-btn tk-cc-btn--outline"
                disabled={reopenLoading}
                onClick={onReopen}
              >
                {reopenLoading ? "Открываю…" : "Переоткрыть"}
              </button>
            ) : null}
          </div>

          {diagOpen && detail.user_id != null ? (
            <FastCheckPanel
              userId={detail.user_id}
              layout="inline"
              hideIdleUI
              initialData={checkCache}
              runNonce={runNonce}
              onResult={onCheckCache}
              onPhaseChange={(p) => setCheckLoading(p === "loading")}
              onDisconnect={onDisconnect}
            />
          ) : null}
        </div>

        <div className="tk-cc-helper__section">
          <div className="tk-cc-helper__section-title">Тикет #{detail.id}</div>
          <div className="tk-cc-meta">
            <div className="tk-cc-meta__row">
              <span className="tk-cc-meta__label">Линия</span>
              <span
                className={`ch-line ch-line--${queueLineBadgeClass(detail.queue_line)}`}
                title={detail.support_line_label}
              >
                {detail.queue_line_label ||
                  queueLineShortLabel(detail.queue_line, detail.support_line)}
              </span>
            </div>
            <div className="tk-cc-meta__row">
              <span className="tk-cc-meta__label">Статус</span>
              <span
                className={
                  statusColumn.kind === "comm"
                    ? `ch-comm ch-comm--${statusColumn.state}`
                    : `ch-status ch-status--${detail.status}`
                }
              >
                {statusColumn.label}
              </span>
            </div>
            <div className="tk-cc-meta__row">
              <span className="tk-cc-meta__label">Приоритет</span>
              <span className="tk-cc-meta__priority-wrap">
                <span
                  ref={prioritySizerRef}
                  className={`tk-cc-meta__priority tk-cc-meta__priority--${priorityMod} tk-cc-meta__priority--sizer`}
                  aria-hidden
                >
                  {currentPriorityLabel}
                </span>
                <select
                  className={`tk-cc-meta__priority tk-cc-meta__priority--${priorityMod}`}
                  value={currentPriority}
                  disabled={priorityLoading}
                  aria-label="Приоритет тикета"
                  style={priorityWidth != null ? { width: priorityWidth } : undefined}
                  onChange={(e) => onChangePriority(e.target.value as TicketPriority)}
                >
                  {PRIORITY_OPTIONS.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </span>
            </div>
            {reopenLabel ? (
              <div className="tk-cc-meta__row">
                <span className="tk-cc-meta__label">Переоткрытие</span>
                <span className="tk-cc-meta__value tk-cc-meta__value--reopened">{reopenLabel}</span>
              </div>
            ) : null}
            {workSince ? (
              <div className="tk-cc-meta__row">
                <span className="tk-cc-meta__label">В работе</span>
                <span className="tk-cc-meta__value">
                  {formatWorkDurationSince(workSince, nowPulse)}
                </span>
              </div>
            ) : null}
            <TicketStaffParticipants
              participants={detail.staff_participants ?? []}
              layout="sidebar"
            />
          </div>
        </div>

        <div className="tk-cc-helper__section tk-cc-helper__section--kb">
          <div className="tk-cc-helper__section-title">Интегрированная база знаний</div>
          <TicketKbSearch onOpenArticle={onOpenKbArticle} />
        </div>
      </section>

      {!kbArticleOpen ? (
        <button
          type="button"
          className="tk-cc-split-handle"
          onClick={onToggle}
          aria-label={collapsed ? "Показать панель абонента" : "Скрыть панель абонента"}
        >
          <span aria-hidden>{collapsed ? "›" : "‹"}</span>
        </button>
      ) : null}
    </div>
  );
}
