type Props = {
  open: boolean;
  userName: string;
  userLogin: string | null;
  busy?: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export default function LogoutConfirmModal({
  open,
  userName,
  userLogin,
  busy = false,
  onClose,
  onConfirm,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="clf-mo open"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="logout-confirm-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="clf-box logout-confirm-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico logout-confirm-modal__ico" aria-hidden>
            ⎋
          </div>
          <div>
            <div className="clf-hd-t" id="logout-confirm-title">
              Выйти из Helpdesk?
            </div>
            <div className="clf-hd-sub">
              {userName}
              {userLogin ? ` · ${userLogin}` : ""}
            </div>
          </div>
        </div>
        <div className="clf-bd">
          <p className="op-admin-hint">
            Текущая сессия будет завершена. Для работы с порталом потребуется войти снова.
          </p>
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" disabled={busy} onClick={onClose}>
            Остаться
          </button>
          <button
            type="button"
            className="clf-btn pri logout-confirm-modal__confirm"
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "Выход…" : "Выйти"}
          </button>
        </div>
      </div>
    </div>
  );
}
