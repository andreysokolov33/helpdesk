import { useEffect, useState } from "react";
import { fetchSuggestedOperatorLogin } from "@/api/operatorsManage";
import { generateOperatorPassword, validateCyrillicFullName } from "@/utils/operatorPassword";

type Props = {
  open: boolean;
  busy: boolean;
  onClose: () => void;
  onSave: (payload: {
    login: string;
    password: string;
    full_name: string;
    email: string | null;
  }) => void | Promise<void>;
};

export default function OperatorCreateModal({ open, busy, onClose, onSave }: Props) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [warn, setWarn] = useState("");
  const [loadingLogin, setLoadingLogin] = useState(false);

  useEffect(() => {
    if (!open) return;
    setPassword(generateOperatorPassword());
    setFullName("");
    setEmail("");
    setWarn("");
    setLoadingLogin(true);
    fetchSuggestedOperatorLogin()
      .then((suggested) => setLogin(suggested))
      .catch(() => setLogin("callcentre1"))
      .finally(() => setLoadingLogin(false));
  }, [open]);

  if (!open) return null;

  function handleSave() {
    const nameErr = validateCyrillicFullName(fullName);
    if (nameErr) {
      setWarn(nameErr);
      return;
    }
    const loginClean = login.trim();
    if (!loginClean) {
      setWarn("Укажите логин");
      return;
    }
    if (!password) {
      setWarn("Сгенерируйте пароль");
      return;
    }
    setWarn("");
    void onSave({
      login: loginClean,
      password,
      full_name: fullName.trim(),
      email: email.trim() || null,
    });
  }

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="op-create-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="clf-box op-admin-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico" aria-hidden>
            ＋
          </div>
          <div>
            <div className="clf-hd-t" id="op-create-title">
              Новый оператор
            </div>
            <div className="clf-hd-sub">Учётная запись линии поддержки</div>
          </div>
        </div>
        <div className="clf-bd">
          <label className="clf-lbl" htmlFor="op-create-login">
            Логин
          </label>
          <input
            id="op-create-login"
            className="clf-inp"
            value={login}
            disabled={busy || loadingLogin}
            onChange={(e) => setLogin(e.target.value)}
            autoComplete="off"
          />

          <label className="clf-lbl" htmlFor="op-create-name">
            ФИО
          </label>
          <input
            id="op-create-name"
            className="clf-inp"
            value={fullName}
            disabled={busy}
            placeholder="Иванов Иван"
            onChange={(e) => setFullName(e.target.value)}
          />

          <label className="clf-lbl" htmlFor="op-create-email">
            Email <span className="op-admin-opt">(необязательно)</span>
          </label>
          <input
            id="op-create-email"
            className="clf-inp"
            type="email"
            value={email}
            disabled={busy}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="off"
          />

          <label className="clf-lbl" htmlFor="op-create-pwd">
            Пароль
          </label>
          <div className="op-admin-pwd-row">
            <input id="op-create-pwd" className="clf-inp op-admin-pwd" readOnly value={password} />
            <button
              type="button"
              className="clf-btn sec"
              disabled={busy}
              onClick={() => setPassword(generateOperatorPassword())}
            >
              Сгенерировать
            </button>
          </div>

          {warn ? <div className="clf-warn">{warn}</div> : null}
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" disabled={busy} onClick={onClose}>
            Отмена
          </button>
          <button type="button" className="clf-btn pri" disabled={busy || loadingLogin} onClick={handleSave}>
            {busy ? "Создаю…" : "Создать"}
          </button>
        </div>
      </div>
    </div>
  );
}
