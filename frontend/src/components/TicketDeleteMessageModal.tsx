type Props = {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  busy?: boolean;
};

export default function TicketDeleteMessageModal({ open, onClose, onConfirm, busy }: Props) {
  if (!open) return null;

  return (
    <div
      className="clf-mo open"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="tk-del-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="clf-box tk-del-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico tk-del-modal__ico" aria-hidden>
            🗑
          </div>
          <div>
            <div className="clf-hd-t" id="tk-del-title">
              Удалить сообщение?
            </div>
            <div className="clf-hd-sub">Действие нельзя отменить. Сообщение исчезнет из переписки.</div>
          </div>
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" disabled={busy} onClick={onClose}>
            Отмена
          </button>
          <button type="button" className="clf-btn pri tk-del-modal__confirm" disabled={busy} onClick={onConfirm}>
            {busy ? "Удаляю…" : "Удалить"}
          </button>
        </div>
      </div>
    </div>
  );
}
