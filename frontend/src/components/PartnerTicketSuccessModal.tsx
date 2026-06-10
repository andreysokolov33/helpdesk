import { useEffect, useRef } from "react";

const REDIRECT_MS = 4000;

type Props = {
  open: boolean;
  ticketId: number;
  onGoHome: () => void;
};

export default function PartnerTicketSuccessModal({ open, ticketId, onGoHome }: Props) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!open) return;
    timerRef.current = setTimeout(onGoHome, REDIRECT_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [open, onGoHome]);

  if (!open) return null;

  function handleGoHome() {
    if (timerRef.current) clearTimeout(timerRef.current);
    onGoHome();
  }

  return (
    <div
      className="clf-mo open call-partner-success-mo"
      role="dialog"
      aria-modal="true"
      aria-labelledby="call-partner-success-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleGoHome();
      }}
    >
      <div className="clf-box call-partner-success">
        <div className="call-partner-success__hero" aria-hidden>
          <span className="call-partner-success__icon">✓</span>
        </div>
        <div className="call-partner-success__body">
          <h2 className="call-partner-success__title" id="call-partner-success-title">
            Заявка передана менеджеру
          </h2>
          <p className="call-partner-success__lead">
            Тикет <span className="call-partner-success__num">№{ticketId}</span> создан и поставлен в очередь
            менеджера. Дальнейшую работу с партнёром продолжит менеджер.
          </p>
          <p className="call-partner-success__hint">
            Переход на главную через несколько секунд…
          </p>
        </div>
        <div className="clf-ft call-partner-success__ft">
          <button type="button" className="clf-btn call-partner-success__btn" onClick={handleGoHome}>
            На главную
          </button>
        </div>
      </div>
    </div>
  );
}
