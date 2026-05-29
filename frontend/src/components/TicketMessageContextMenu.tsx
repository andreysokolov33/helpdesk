import { useEffect, useRef } from "react";
import type { TicketMessage } from "@/api/ticket";
import { isOwnTicketMessage } from "@/utils/ticketMessages";

export type MessageMenuAction = "copy" | "reply" | "edit" | "delete";

type Props = {
  x: number;
  y: number;
  message: TicketMessage;
  onAction: (action: MessageMenuAction, message: TicketMessage) => void;
  onClose: () => void;
  allowReply?: boolean;
  /** Служебные комментарии: только изменить / удалить (своё сообщение). */
  commentMode?: boolean;
};

export default function TicketMessageContextMenu({
  x,
  y,
  message,
  onAction,
  onClose,
  allowReply = true,
  commentMode = false,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const own = isOwnTicketMessage(message.side);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onPointer = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [onClose]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const pad = 8;
    const rect = el.getBoundingClientRect();
    let left = x;
    let top = y;
    if (left + rect.width > window.innerWidth - pad) {
      left = Math.max(pad, window.innerWidth - rect.width - pad);
    }
    if (top + rect.height > window.innerHeight - pad) {
      top = Math.max(pad, window.innerHeight - rect.height - pad);
    }
    el.style.left = `${left}px`;
    el.style.top = `${top}px`;
  }, [x, y]);

  if (commentMode) {
    return (
      <div ref={ref} className="tk-msg-menu" style={{ left: x, top: y }} role="menu">
        <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("edit", message)}>
          Изменить
        </button>
        <button
          type="button"
          className="tk-msg-menu__item tk-msg-menu__item--danger"
          role="menuitem"
          onClick={() => onAction("delete", message)}
        >
          Удалить
        </button>
      </div>
    );
  }

  return (
    <div ref={ref} className="tk-msg-menu" style={{ left: x, top: y }} role="menu">
      <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("copy", message)}>
        Копировать
      </button>
      {allowReply ? (
        <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("reply", message)}>
          Ответить
        </button>
      ) : null}
      {own ? (
        <>
          <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("edit", message)}>
            Изменить
          </button>
          <button
            type="button"
            className="tk-msg-menu__item tk-msg-menu__item--danger"
            role="menuitem"
            onClick={() => onAction("delete", message)}
          >
            Удалить
          </button>
        </>
      ) : null}
    </div>
  );
}
