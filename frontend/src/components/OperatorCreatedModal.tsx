import { useEffect, useMemo, useState } from "react";

export type OperatorCredsVariant = "created" | "password";

type Props = {
  open: boolean;
  variant: OperatorCredsVariant;
  login: string;
  password: string;
  fullName: string;
  onClose: () => void;
};

export function formatOperatorCredentialsText(login: string, password: string): string {
  return `Логин: ${login}\nПароль: ${password}`;
}

export default function OperatorCreatedModal({
  open,
  variant,
  login,
  password,
  fullName,
  onClose,
}: Props) {
  const [copied, setCopied] = useState(false);

  const credentialsText = useMemo(
    () => formatOperatorCredentialsText(login, password),
    [login, password],
  );

  useEffect(() => {
    if (!open) setCopied(false);
  }, [open]);

  if (!open) return null;

  const title = variant === "created" ? "Оператор создан" : "Пароль изменён";

  async function copyCredentials() {
    try {
      await navigator.clipboard.writeText(credentialsText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may be unavailable */
    }
  }

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
            Скопируйте данные сейчас — больше они не отобразятся.
          </p>

          <pre className="op-admin-cred-pre">{credentialsText}</pre>

          <button type="button" className="clf-btn pri op-admin-cred-copy" onClick={() => void copyCredentials()}>
            {copied ? "Скопировано" : "Копировать в буфер"}
          </button>
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" onClick={onClose}>
            Готово
          </button>
        </div>
      </div>
    </div>
  );
}
