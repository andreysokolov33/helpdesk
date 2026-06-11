import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { TicketDetail } from "@/api/ticket";
import type { FastCheckResponse, UserProfileResponse } from "@/api/userProfile";
import FastCheckPanel from "@/components/FastCheckPanel";
import TicketStaffParticipants from "@/components/TicketStaffParticipants";
import { ticketListStatusColumn } from "@/api/tracker";
import { formatWorkDurationSince } from "@/utils/ticketFormat";
import { queueLineBadgeClass, queueLineShortLabel } from "@/utils/ticketLabels";

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
  onTransfer: () => void;
  onTakeBack: () => void;
  onReopen: () => void;
  onLinkSubscriber: () => void;
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
  onTransfer,
  onTakeBack,
  onReopen,
  onLinkSubscriber,
}: Props) {
  const [diagOpen, setDiagOpen] = useState(false);
  const [runNonce, setRunNonce] = useState(0);
  const [checkLoading, setCheckLoading] = useState(false);

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

  return (
    <div className="tk-cc-helper-wrap">
      <section
        className={`tk-cc-helper${collapsed ? " tk-cc-helper--collapsed" : ""}`}
        aria-label="Данные абонента и тикета"
      >
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
                className="tk-cc-btn tk-cc-btn--outline"
                disabled={transferLoading}
                onClick={onTransfer}
              >
                {transferLoading ? "Передаю…" : "Передать инженерам"}
              </button>
            ) : detail.is_open && detail.queue_line === "engineers" ? (
              <button
                type="button"
                className="tk-cc-btn tk-cc-btn--outline"
                disabled={takeBackLoading}
                onClick={onTakeBack}
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
          <div className="tk-cc-kb-stub">
            <input
              type="search"
              className="tk-cc-kb-stub__search"
              placeholder="Поиск решений…"
              disabled
              aria-disabled
            />
            <p className="tk-cc-kb-stub__note">Раздел в разработке</p>
          </div>
        </div>
      </section>

      <button
        type="button"
        className="tk-cc-split-handle"
        onClick={onToggle}
        aria-label={collapsed ? "Показать панель абонента" : "Скрыть панель абонента"}
      >
        <span aria-hidden>{collapsed ? "›" : "‹"}</span>
      </button>
    </div>
  );
}
