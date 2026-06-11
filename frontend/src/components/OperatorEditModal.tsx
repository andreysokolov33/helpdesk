import { useEffect, useState } from "react";
import type { OperatorManageItem } from "@/api/operatorsManage";
import { generateOperatorPassword, validateCyrillicFullName } from "@/utils/operatorPassword";

type Props = {
  open: boolean;
  operator: OperatorManageItem | null;
  busy: boolean;
  onClose: () => void;
  onSaveName: (fullName: string) => void | Promise<void>;
  onSavePassword: (password: string) => void | Promise<void>;
  onArchive: () => void | Promise<void>;
  onRestore: () => void | Promise<void>;
};

export default function OperatorEditModal({
  open,
  operator,
  busy,
  onClose,
  onSaveName,
  onSavePassword,
  onArchive,
  onRestore,
}: Props) {
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordMode, setPasswordMode] = useState(false);
  const [warn, setWarn] = useState("");

  useEffect(() => {
    if (!open || !operator) return;
    setFullName(operator.full_name || "");
    setPassword("");
    setPasswordMode(false);
    setWarn("");
  }, [open, operator]);

  if (!open || !operator) return null;

  const isAdmin = operator.level === 2;

  function handleSaveName() {
    const err = validateCyrillicFullName(fullName);
    if (err) {
      setWarn(err);
      return;
    }
    setWarn("");
    void onSaveName(fullName.trim());
  }

  function startPasswordChange() {
    setPassword(generateOperatorPassword());
    setPasswordMode(true);
    setWarn("");
  }

  function cancelPasswordChange() {
    setPassword("");
    setPasswordMode(false);
    setWarn("");
  }

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="op-edit-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="clf-box op-admin-modal">
        <div className="clf-hd">
          <div className="clf-hd-ico" aria-hidden>
            ✎
          </div>
          <div>
            <div className="clf-hd-t" id="op-edit-title">
              Редактирование
            </div>
            <div className="clf-hd-sub">{operator.login}</div>
          </div>
        </div>
        <div className="clf-bd">
          <label className="clf-lbl" htmlFor="op-edit-name">
            ФИО
          </label>
          <input
            id="op-edit-name"
            className="clf-inp"
            value={fullName}
            disabled={busy}
            placeholder="Иванов Иван"
            onChange={(e) => setFullName(e.target.value)}
          />

          <div className="op-admin-edit-section">
            <div className="clf-lbl">Пароль</div>
            {!passwordMode ? (
              <button type="button" className="clf-btn sec" disabled={busy} onClick={startPasswordChange}>
                Сменить пароль
              </button>
            ) : (
              <>
                <p className="op-admin-hint">
                  Новый пароль будет показан отдельно после сохранения — скопируйте его сразу.
                </p>
                <div className="op-admin-pwd-row">
                  <input className="clf-inp op-admin-pwd" readOnly value={password} />
                  <button
                    type="button"
                    className="clf-btn sec"
                    disabled={busy}
                    onClick={() => setPassword(generateOperatorPassword())}
                  >
                    Сгенерировать
                  </button>
                </div>
                <div className="op-admin-pwd-actions">
                  <button type="button" className="clf-btn sec" disabled={busy} onClick={cancelPasswordChange}>
                    Отмена
                  </button>
                  <button
                    type="button"
                    className="clf-btn pri"
                    disabled={busy || !password}
                    onClick={() => void onSavePassword(password)}
                  >
                    {busy ? "Сохраняю…" : "Сохранить пароль"}
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="op-admin-status-row">
            <span className="clf-lbl">Статус</span>
            <span className={`op-admin-badge ${operator.is_active ? "op-admin-badge--on" : "op-admin-badge--off"}`}>
              {operator.is_active ? "Активен" : "В архиве"}
            </span>
          </div>

          {!isAdmin ? (
            <div className="op-admin-archive-row">
              {operator.is_active ? (
                <button
                  type="button"
                  className="clf-btn sec op-admin-archive-btn"
                  disabled={busy}
                  onClick={() => void onArchive()}
                >
                  {busy ? "…" : "Архивировать"}
                </button>
              ) : (
                <button type="button" className="clf-btn sec" disabled={busy} onClick={() => void onRestore()}>
                  {busy ? "…" : "Восстановить из архива"}
                </button>
              )}
            </div>
          ) : (
            <p className="op-admin-hint">Администратора нельзя архивировать с этой страницы.</p>
          )}

          {warn ? <div className="clf-warn">{warn}</div> : null}
        </div>
        <div className="clf-ft">
          <button type="button" className="clf-btn sec" disabled={busy} onClick={onClose}>
            Закрыть
          </button>
          <button type="button" className="clf-btn pri" disabled={busy} onClick={handleSaveName}>
            {busy ? "Сохраняю…" : "Сохранить ФИО"}
          </button>
        </div>
      </div>
    </div>
  );
}
