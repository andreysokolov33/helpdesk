import { useCallback, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

type Props = {
  hotspotAddress: string | null | undefined;
};

type Placement = "bottom" | "top";

const GAP = 10;
const VIEWPORT_PAD = 14;
const POPOVER_WIDTH = 360;

function HelpIcon() {
  return (
    <svg className="up-help-icon" viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.75" />
      <line
        x1="12"
        y1="7.25"
        x2="12"
        y2="13.25"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
      />
      <circle cx="12" cy="16.75" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function AuthPageHelp({ hotspotAddress }: Props) {
  const tipId = useId();
  const addr = hotspotAddress?.trim() || null;
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
  }, [open, updatePosition, addr]);

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
      <div className="up-help-title">Инструкция для абонента: вход в Wi‑Fi</div>
      <div className="up-help-body">
        <ol className="up-help-steps">
          <li>
            <span className="up-help-step-name">Подключение к сети</span>
            <p>
              Попросите подключиться к Wi‑Fi нашей сети. В названии сети обычно есть{" "}
              <strong>WFTK</strong>, <strong>Wifitochka</strong> или <strong>FREEWIFI</strong>.
            </p>
            <p>
              После подключения на телефоне должна <strong>сама открыться</strong> страница авторизации — абонент
              вводит <strong>логин и пароль</strong> из договора.
            </p>
          </li>
          <li>
            <span className="up-help-step-name">Страница не открылась сама</span>
            <p>
              Убедитесь, что Wi‑Fi подключен. Откройте <strong>любой браузер</strong> и в{" "}
              <strong>адресной строке</strong> (не в поиске Google/Yandex) введите адрес страницы авторизации:
            </p>
            {addr ? (
              <span className="up-help-addr-line" title={addr}>
                <code className="up-help-addr">{addr}</code>
              </span>
            ) : (
              <p className="up-help-note">
                Адрес не указан в карточке — уточните у коллег или в АБС. После ввода адреса должна открыться страница
                входа.
              </p>
            )}
            {addr ? <p>После перехода по адресу должна открыться страница авторизации.</p> : null}
          </li>
          <li>
            <span className="up-help-step-name">Адрес в браузере не открывается</span>
            <p>
              Попросите зайти в личный кабинет:{" "}
              <a href="https://lk.wifitochka.ru" target="_blank" rel="noopener noreferrer" className="up-help-link">
                lk.wifitochka.ru
              </a>
              , войти под логином абонента и на главной нажать <strong>«Включить интернет»</strong>. Должна открыться
              страница авторизации.
            </p>
          </li>
        </ol>
      </div>
    </div>
  ) : null;

  return (
    <span className="up-help-wrap" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      <button
        ref={btnRef}
        type="button"
        className="up-help-btn"
        aria-label="Инструкция: как авторизовать абонента в Wi‑Fi"
        aria-describedby={open ? tipId : undefined}
      >
        <HelpIcon />
      </button>
      {popover ? createPortal(popover, document.body) : null}
    </span>
  );
}
