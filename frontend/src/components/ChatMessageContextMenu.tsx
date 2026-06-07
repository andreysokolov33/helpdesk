import { useEffect, useLayoutEffect, useRef } from "react";

export type ChatMenuAction = "copy" | "reply" | "edit" | "delete";

type Props = {
  x: number;
  y: number;
  own: boolean;
  onAction: (action: ChatMenuAction) => void;
  onClose: () => void;
};

export default function ChatMessageContextMenu({ x, y, own, onAction, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);

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

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const pad = 8;
    const rect = el.getBoundingClientRect();
    let left = x;
    let top = y;
    if (left + rect.width > window.innerWidth - pad) left = Math.max(pad, window.innerWidth - rect.width - pad);
    if (top + rect.height > window.innerHeight - pad) top = Math.max(pad, window.innerHeight - rect.height - pad);
    el.style.left = `${left}px`;
    el.style.top = `${top}px`;
  }, [x, y]);

  return (
    <div ref={ref} className="tk-msg-menu" style={{ left: x, top: y }} role="menu">
      <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("copy")}>
        Копировать
      </button>
      <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("reply")}>
        Ответить
      </button>
      {own ? (
        <>
          <button type="button" className="tk-msg-menu__item" role="menuitem" onClick={() => onAction("edit")}>
            Изменить
          </button>
          <button
            type="button"
            className="tk-msg-menu__item tk-msg-menu__item--danger"
            role="menuitem"
            onClick={() => onAction("delete")}
          >
            Удалить
          </button>
        </>
      ) : null}
    </div>
  );
}
