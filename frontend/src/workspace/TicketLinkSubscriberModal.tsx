import { useState } from "react";
import SubscriberSearchField from "@/components/SubscriberSearchField";
import type { SubscriberSearchHit } from "@/api/search";
import { linkTicketSubscriber } from "@/api/ticket";
import type { TicketDetail } from "@/api/ticket";

type Props = {
  open: boolean;
  ticketId: number;
  onClose: () => void;
  onLinked: (detail: TicketDetail) => void;
};

export default function TicketLinkSubscriberModal({ open, ticketId, onClose, onLinked }: Props) {
  const [subscriber, setSubscriber] = useState<SubscriberSearchHit | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit() {
    if (!subscriber) {
      setError("Выберите абонента");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const detail = await linkTicketSubscriber(ticketId, subscriber.id);
      setSubscriber(null);
      onLinked(detail);
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось привязать абонента");
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    if (submitting) return;
    setSubscriber(null);
    setError(null);
    onClose();
  }

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tk-link-sub-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div className="clf-box tk-link-sub-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico" aria-hidden>
            🔍
          </div>
          <div>
            <div className="clf-hd-t" id="tk-link-sub-title">
              Найти абонента
            </div>
            <div className="clf-hd-sub">Привязка к тикету #{ticketId}</div>
          </div>
        </div>

        <div className="clf-bd">
          <div className="call-field">
            <label className="call-field__lbl">Абонент</label>
            <SubscriberSearchField selected={subscriber} onSelect={setSubscriber} />
          </div>
          {error ? (
            <div className="call-error" role="alert">
              {error}
            </div>
          ) : null}
        </div>

        <div className="clf-ft">
          <button type="button" className="clf-btn" onClick={handleClose} disabled={submitting}>
            Отмена
          </button>
          <button type="button" className="clf-btn pri" onClick={() => void handleSubmit()} disabled={submitting}>
            {submitting ? "Сохраняем…" : "Привязать"}
          </button>
        </div>
      </div>
    </div>
  );
}
