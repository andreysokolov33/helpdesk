function openTicketsPhrase(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} открытый тикет`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${count} открытых тикета`;
  }
  return `${count} открытых тикетов`;
}

type Props = {
  open: boolean;
  operatorName: string;
  operatorLogin: string;
  restore: boolean;
  openTicketsCount?: number;
  busy?: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export default function OperatorArchiveConfirmModal({
  open,
  operatorName,
  operatorLogin,
  restore,
  openTicketsCount = 0,
  busy = false,
  onClose,
  onConfirm,
}: Props) {
  if (!open) return null;

  const title = restore ? "Восстановить оператора?" : "Архивировать оператора?";

  return (
    <div
      className="clf-mo open"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="op-archive-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="clf-box op-admin-archive-modal">
        <div className="clf-hd">
          <div className={`clf-hd-ico op-admin-archive-modal__ico${restore ? " op-admin-archive-modal__ico--restore" : ""}`} aria-hidden>
            {restore ? "↺" : "📦"}
          </div>
          <div>
            <div className="clf-hd-t" id="op-archive-title">
              {title}
            </div>
            <div className="clf-hd-sub">
              {operatorName}
              {operatorLogin ? ` · ${operatorLogin}` : ""}
            </div>
          </div>
        </div>
        <div className="clf-bd">
          {restore ? (
            <p className="op-admin-hint">
              Оператор снова сможет войти в Helpdesk. Текущие сессии не восстанавливаются — потребуется новый вход.
            </p>
          ) : (
            <>
              <p className="op-admin-hint op-admin-hint--warn">
                Вход будет заблокирован, активные сессии завершатся. Оператор сразу потеряет доступ к порталу.
              </p>
              {openTicketsCount > 0 ? (
                <p className="op-admin-hint op-admin-hint--warn">
                  У данного оператора {openTicketsPhrase(openTicketsCount)}. Они будут распределены между
                  другими операторами.
                </p>
              ) : null}
            </>
          )}
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" disabled={busy} onClick={onClose}>
            Отмена
          </button>
          <button
            type="button"
            className={`clf-btn pri${restore ? "" : " op-admin-archive-modal__confirm"}`}
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "…" : restore ? "Восстановить" : "Архивировать"}
          </button>
        </div>
      </div>
    </div>
  );
}
