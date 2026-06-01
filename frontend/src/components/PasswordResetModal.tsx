import { useCallback, useEffect, useState } from "react";
import {
  fetchPasswordResetPoll,
  fetchPasswordResetState,
  generatePasswordResetCode,
  type PasswordResetState,
} from "@/api/userProfile";

const POLL_MS = 3000;

type Props = {
  userId: number;
  busy: boolean;
  setBusy: (v: boolean) => void;
  onClose: () => void;
  onError: (msg: string) => void;
};

function fmtCountdown(ms: number): string {
  if (ms <= 0) return "00:00";
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function PasswordResetModal({ userId, busy, setBusy, onClose, onError }: Props) {
  const [state, setState] = useState<PasswordResetState | null>(null);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [trackingCodeId, setTrackingCodeId] = useState<number | null>(null);
  const [codeUsedBySubscriber, setCodeUsedBySubscriber] = useState(false);
  const [nowTs, setNowTs] = useState(() => Date.now());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const s = await fetchPasswordResetState(userId);
      setState(s);
      setCode(s.active_code);
      setExpiresAt(s.expires_at ? new Date(s.expires_at) : null);
      if (s.code_id) {
        setTrackingCodeId(s.code_id);
      }
      setCodeUsedBySubscriber(false);
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [userId, onError]);

  const pollStatus = useCallback(async () => {
    if (!trackingCodeId || codeUsedBySubscriber) return;
    try {
      const s = await fetchPasswordResetPoll(userId, trackingCodeId);
      if (s.code_used) {
        setCodeUsedBySubscriber(true);
        setCode(null);
        setExpiresAt(null);
        return;
      }
      if (s.code_expired) {
        setCode(null);
        setExpiresAt(null);
        setTrackingCodeId(null);
        return;
      }
      if (s.active_code && s.expires_at) {
        setCode(s.active_code);
        setExpiresAt(new Date(s.expires_at));
      }
    } catch {
      /* поллинг не мешает работе оператора */
    }
  }, [userId, trackingCodeId, codeUsedBySubscriber]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const t = window.setInterval(() => setNowTs(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    if (!trackingCodeId || codeUsedBySubscriber) return;
    void pollStatus();
    const t = window.setInterval(() => void pollStatus(), POLL_MS);
    return () => window.clearInterval(t);
  }, [trackingCodeId, codeUsedBySubscriber, pollStatus]);

  const remainingMs = expiresAt ? expiresAt.getTime() - nowTs : 0;
  const codeActive = Boolean(code && expiresAt && remainingMs > 0 && !codeUsedBySubscriber);

  useEffect(() => {
    if (expiresAt && remainingMs <= 0 && code && !codeUsedBySubscriber) {
      setCode(null);
      setExpiresAt(null);
      void load();
    }
  }, [remainingMs, expiresAt, code, codeUsedBySubscriber, load]);

  async function onGenerate() {
    setBusy(true);
    setCodeUsedBySubscriber(false);
    try {
      const r = await generatePasswordResetCode(userId);
      setCode(r.code);
      setExpiresAt(new Date(r.expires_at));
      setTrackingCodeId(r.code_id);
      setState((prev) =>
        prev
          ? {
              ...prev,
              active_code: r.code,
              expires_at: r.expires_at,
              can_generate: false,
              code_id: r.code_id,
            }
          : prev,
      );
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : "Не удалось сгенерировать код");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="up-modal up-modal--pwd-reset" onClick={(e) => e.stopPropagation()}>
      <div className="up-modal-title">Смена пароля абонента</div>

      {loading ? (
        <p className="up-muted">Загрузка…</p>
      ) : (
        <>
          {state?.has_ppp_sessions ? (
            <div className="up-alert warn up-pwd-ppp-warn" role="alert">
              Судя по сессиям данного абонента, он выходит в интернет в том числе и через PPPoE
              подключение. Значит, у него на роутере прописан логин и пароль для автоматической
              авторизации в сети, поэтому смена пароля приведёт к тому, что роутер не сможет
              авторизоваться. Придётся зайти в настройки роутера и ввести новый пароль в настройках
              PPPoE.
            </div>
          ) : null}

          <div className="up-pwd-instructions">
            <div className="up-pwd-instructions-title">Инструкция для оператора</div>
            <ol className="up-pwd-steps">
              <li>
                Попросите абонента зайти в личный кабинет на <strong>страницу авторизации</strong>,
                нажать «Забыл пароль» и выбрать «У меня есть код для восстановления». У абонента
                появится поле для ввода <strong>4 цифр</strong>.
              </li>
              <li>
                Нажмите кнопку <strong>«Сгенерировать код»</strong> ниже. На экране появится код из
                4 цифр — продиктуйте его абоненту.
              </li>
              <li>
                После правильного ввода кода абонент перейдёт на страницу <strong>нового пароля</strong>.
                После успешной смены пароля ему нужно будет <strong>заново авторизоваться</strong> в
                сети.
              </li>
            </ol>
          </div>

          {codeUsedBySubscriber ? (
            <div className="up-alert ok up-pwd-used-success" role="status">
              Абонент успешно воспользовался кодом и попал на страницу ввода нового пароля
            </div>
          ) : null}

          {codeActive ? (
            <div className="up-pwd-code-block">
              <div className="up-pwd-code-label">Код для абонента</div>
              <div className="up-pwd-code-digits" aria-live="polite">
                {code}
              </div>
              <div className="up-pwd-timer">
                Действует ещё: <strong>{fmtCountdown(remainingMs)}</strong>
              </div>
            </div>
          ) : null}

          <div className="up-modal-actions up-modal-actions--stack">
            <button
              type="button"
              className="up-btn pri up-pwd-generate-btn"
              disabled={busy || codeActive || codeUsedBySubscriber}
              onClick={() => void onGenerate()}
            >
              Сгенерировать код
            </button>
            <button type="button" className="up-btn sec" disabled={busy} onClick={onClose}>
              Закрыть
            </button>
          </div>
        </>
      )}
    </div>
  );
}
