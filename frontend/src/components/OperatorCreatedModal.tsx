import { useEffect, useState } from "react";

export type OperatorCredsVariant = "created" | "password";

type Props = {
  open: boolean;
  variant: OperatorCredsVariant;
  login: string;
  password: string;
  fullName: string;
  onClose: () => void;
};

type CopiedField = "login" | "password" | "all" | null;

export default function OperatorCreatedModal({
  open,
  variant,
  login,
  password,
  fullName,
  onClose,
}: Props) {
  const [copied, setCopied] = useState<CopiedField>(null);

  useEffect(() => {
    if (!open) setCopied(null);
  }, [open]);

  if (!open) return null;

  const title = variant === "created" ? "Оператор создан" : "Пароль изменён";

  async function copyText(text: string, field: CopiedField) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(field);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      /* clipboard may be unavailable */
    }
  }

  const allText = `Логин: ${login}\nПароль: ${password}`;

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="op-created-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="clf-box op-admin-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico" aria-hidden>
            ✓
          </div>
          <div>
            <div className="clf-hd-t" id="op-created-title">
              {title}
            </div>
            <div className="clf-hd-sub">{fullName}</div>
          </div>
        </div>
        <div className="clf-bd">
          <p className="op-admin-hint op-admin-hint--warn">
            Скопируйте логин и пароль сейчас — больше они не отобразятся.
          </p>

          <label className="clf-lbl" htmlFor="op-created-login">
            Логин
          </label>
          <div className="op-admin-cred-row">
            <input id="op-created-login" className="clf-inp op-admin-pwd" readOnly value={login} />
            <button type="button" className="clf-btn sec" onClick={() => void copyText(login, "login")}>
              {copied === "login" ? "Скопировано" : "Копировать"}
            </button>
          </div>

          <label className="clf-lbl" htmlFor="op-created-pwd">
            Пароль
          </label>
          <div className="op-admin-cred-row">
            <input id="op-created-pwd" className="clf-inp op-admin-pwd" readOnly value={password} />
            <button type="button" className="clf-btn sec" onClick={() => void copyText(password, "password")}>
              {copied === "password" ? "Скопировано" : "Копировать"}
            </button>
          </div>
        </div>
        <div className="clf-ft op-admin-created-ft">
          <button type="button" className="clf-btn sec" onClick={() => void copyText(allText, "all")}>
            {copied === "all" ? "Скопировано" : "Скопировать всё"}
          </button>
          <button type="button" className="clf-btn pri" onClick={onClose}>
            Готово
          </button>
        </div>
      </div>
    </div>
  );
}
