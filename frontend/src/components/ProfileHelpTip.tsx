import { useCallback, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

type Placement = "bottom" | "top";

const GAP = 10;
const VIEWPORT_PAD = 14;
const POPOVER_WIDTH = 360;

type Props = {
  title: string;
  ariaLabel: string;
  children: ReactNode;
  /** Компактная иконка для строк KV-карточки */
  compact?: boolean;
};

function QuestionIcon({ compact }: { compact?: boolean }) {
  return (
    <svg
      className={compact ? "up-help-icon up-help-icon--sm" : "up-help-icon"}
      viewBox="0 0 24 24"
      aria-hidden
    >
      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.75" />
      <path
        d="M9.2 9.4a2.85 2.85 0 0 1 5.55.95c0 1.7-1.55 2.35-2.55 2.95-.7.42-1.05.8-1.05 1.45"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.85"
        strokeLinecap="round"
      />
      <circle cx="12" cy="17.35" r="1.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ProfileHelpTip({ title, ariaLabel, children, compact }: Props) {
  const tipId = useId();
  const btnRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState<Placement>("bottom");
  const [coords, setCoords] = useState({ top: 0, left: 0, width: POPOVER_WIDTH, maxHeight: 400 });
  const [arrowX, setArrowX] = useState(0);

  const updatePosition = useCallback(() => {
    const btn = btnRef.current;
    const pop = popRef.current;
    if (!btn || !pop) return;

    const btnRect = btn.getBoundingClientRect();
    const popRect = pop.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const width = Math.min(POPOVER_WIDTH, vw - VIEWPORT_PAD * 2);
    const popH = popRect.height || pop.offsetHeight;

    const spaceBelow = vh - btnRect.bottom - GAP - VIEWPORT_PAD;
    const spaceAbove = btnRect.top - GAP - VIEWPORT_PAD;
    const placeBelow = spaceBelow >= popH || spaceBelow >= spaceAbove;

    const maxHeight = Math.max(120, vh - VIEWPORT_PAD * 2);
    let top: number;

    if (placeBelow) {
      top = btnRect.bottom + GAP;
      if (top + popH > vh - VIEWPORT_PAD) {
        top = Math.max(VIEWPORT_PAD, vh - VIEWPORT_PAD - popH);
      }
      setPlacement("bottom");
    } else {
      top = btnRect.top - GAP - popH;
      if (top < VIEWPORT_PAD) {
        top = VIEWPORT_PAD;
      }
      setPlacement("top");
    }

    let left = btnRect.right - width;
    left = Math.max(VIEWPORT_PAD, Math.min(left, vw - VIEWPORT_PAD - width));

    const arrowCenter = btnRect.left + btnRect.width / 2 - left;
    setArrowX(Math.max(12, Math.min(width - 12, arrowCenter)));
    setCoords({ top, left, width, maxHeight });
  }, []);

  const show = useCallback(() => {
    if (hideTimer.current) {
      clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
    setOpen(true);
  }, []);

  const hide = useCallback(() => {
    hideTimer.current = setTimeout(() => setOpen(false), 120);
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
    const raf = requestAnimationFrame(updatePosition);
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open, updatePosition, children]);

  const popover = open ? (
    <div
      id={tipId}
      ref={popRef}
      className={`up-help-popover up-help-popover--open up-help-popover--${placement}`}
      role="tooltip"
      style={{
        top: coords.top,
        left: coords.left,
        width: coords.width,
        maxHeight: coords.maxHeight,
        ["--up-help-arrow-x" as string]: `${arrowX}px`,
      }}
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      <div className="up-help-title">{title}</div>
      <div className="up-help-body">{children}</div>
    </div>
  ) : null;

  return (
    <span className="up-help-wrap" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      <button
        ref={btnRef}
        type="button"
        className={compact ? "up-help-btn up-help-btn--compact" : "up-help-btn"}
        aria-label={ariaLabel}
        aria-describedby={open ? tipId : undefined}
      >
        <QuestionIcon compact={compact} />
      </button>
      {popover ? createPortal(popover, document.body) : null}
    </span>
  );
}
