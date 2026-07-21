import { useEffect, type ReactNode } from "react";
import CallCenterPhoneIcon from "@/components/CallCenterPhoneIcon";

type Props = {
  open: boolean;
  onClose: () => void;
  closedMode: boolean;
};

function HelpSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="ch-help-section">
      <h3 className="ch-help-section__title">{title}</h3>
      {children}
    </section>
  );
}

function HelpItem({ badge, text }: { badge: ReactNode; text: string }) {
  return (
    <div className="ch-help-item">
      <span className="ch-help-item__badge">{badge}</span>
      <span className="ch-help-item__text">{text}</span>
    </div>
  );
}

export default function TicketsListHelpDrawer({ open, onClose, closedMode }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      <div
        className={`ch-help-backdrop${open ? " ch-help-backdrop--open" : ""}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside
        className={`ch-help-drawer${open ? " ch-help-drawer--open" : ""}`}
        aria-label="Справка по списку тикетов"
        aria-hidden={!open}
      >
        <div className="ch-help-drawer__head">
          <span className="ch-help-drawer__title">Справка</span>
          <button type="button" className="ch-help-drawer__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="ch-help-drawer__body">
          {!closedMode ? (
            <HelpSection title="Приоритет">
              <HelpItem
                badge={<span className="ch-priority ch-priority--low">Низкий</span>}
                text="низкая срочность"
              />
              <HelpItem
                badge={<span className="ch-priority ch-priority--middle">Средний</span>}
                text="стандартный, по умолчанию"
              />
              <HelpItem
                badge={<span className="ch-priority ch-priority--high">Высокий</span>}
                text="повышенная срочность"
              />
              <HelpItem
                badge={<span className="ch-priority ch-priority--critical">Критический</span>}
                text="максимальная срочность"
              />
            </HelpSection>
          ) : null}

          <HelpSection title="Статус">
            {!closedMode ? (
              <>
                <p className="ch-help-subhead">Коммуникация</p>
                <HelpItem
                  badge={<span className="ch-comm ch-comm--needs_reply">Нужен ответ</span>}
                  text="ожидается ответ оператора"
                />
                <HelpItem
                  badge={<span className="ch-comm ch-comm--awaiting_subscriber">Ждём абонента</span>}
                  text="ответ отправлен, ждём абонента"
                />
                <p className="ch-help-subhead">Рабочий статус</p>
              </>
            ) : null}
            <HelpItem
              badge={<span className="ch-status ch-status--pending">Ожидает</span>}
              text="ещё не взят в работу"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--open">Открыт</span>}
              text="активно обрабатывается"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--in_progress">В работе</span>}
              text="активно обрабатывается"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--resolved">Решён</span>}
              text="проблема решена"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--closed">Закрыт</span>}
              text="тикет завершён"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--deferred">Отложен</span>}
              text="отложен без решения"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--cancelled">Отменён</span>}
              text="тикет отменён"
            />
            <HelpItem
              badge={<span className="ch-status ch-status--not_resolved">Нерешён</span>}
              text="закрыт без решения"
            />
          </HelpSection>

          {!closedMode ? (
            <HelpSection title="Выделение строки">
              <div className="ch-help-item ch-help-item--highlight">
                <span className="ch-help-item__badge ch-row--unread ch-help-highlight-strip" aria-hidden />
                <span className="ch-help-item__text">
                  красноватый фон — непрочитанные сообщения или нужен ответ на вашей линии
                </span>
              </div>
            </HelpSection>
          ) : null}

          <HelpSection title="Значки">
            <div className="ch-help-item">
              <span className="ch-help-item__badge">
                <span className="ch-call-ico" aria-hidden>
                  <CallCenterPhoneIcon />
                </span>
              </span>
              <span className="ch-help-item__text">зарегистрирован после звонка на горячую линию</span>
            </div>
            <div className="ch-help-item">
              <span className="ch-help-item__badge">
                <span className="ch-jur-mark">ЮЛ</span>
              </span>
              <span className="ch-help-item__text">абонент — юридическое лицо</span>
            </div>
          </HelpSection>
        </div>
      </aside>
    </>
  );
}
