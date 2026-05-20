import { useEffect } from "react";
import { createPortal } from "react-dom";

export type ToastVariant = "success" | "error";

type Props = {
  message: string;
  variant?: ToastVariant;
  onClose: () => void;
  durationMs?: number;
};

export default function ToastNotice({
  message,
  variant = "success",
  onClose,
  durationMs = 4500,
}: Props) {
  useEffect(() => {
    const t = window.setTimeout(onClose, durationMs);
    return () => window.clearTimeout(t);
  }, [message, durationMs, onClose]);

  return createPortal(
    <div className="hd-toast-stack" role="region" aria-label="Уведомления">
      <div className={`hd-toast hd-toast--${variant}`} role="status">
        <span className="hd-toast__text">{message}</span>
        <button type="button" className="hd-toast__close" aria-label="Закрыть" onClick={onClose}>
          ×
        </button>
      </div>
    </div>,
    document.body,
  );
}
