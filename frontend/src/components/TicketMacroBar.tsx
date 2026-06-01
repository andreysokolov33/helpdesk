import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { fetchHelpdeskMacros, type HelpdeskMacro } from "@/api/macros";

const CHIP_GAP = 4;
const MIN_VISIBLE = 1;

export type TicketChatPanelMode = "subscriber" | "comments";

type Props = {
  disabled?: boolean;
  /** Без быстрых ответов (тикет не ЛК или закрыт) — при наличии onChatPanelChange остаётся переключатель. */
  hideMacros?: boolean;
  onPick: (macro: HelpdeskMacro) => void;
  chatPanel?: TicketChatPanelMode;
  onChatPanelChange?: (mode: TicketChatPanelMode) => void;
  subscriberUnreadCount?: number;
};

export default function TicketMacroBar({
  disabled = false,
  hideMacros = false,
  onPick,
  chatPanel,
  onChatPanelChange,
  subscriberUnreadCount = 0,
}: Props) {
  const [macros, setMacros] = useState<HelpdeskMacro[]>([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const rowRef = useRef<HTMLDivElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hideMacros) {
      setMacros([]);
      setVisibleCount(0);
      return;
    }
    let cancelled = false;
    void fetchHelpdeskMacros()
      .then((items) => {
        if (!cancelled) {
          setMacros(items);
          setVisibleCount(items.length);
        }
      })
      .catch(() => {
        if (!cancelled) setMacros([]);
      });
    return () => {
      cancelled = true;
    };
  }, [hideMacros]);

  useLayoutEffect(() => {
    setMenuOpen(false);
  }, [visibleCount]);

  useLayoutEffect(() => {
    if (!macros.length) {
      setVisibleCount(0);
      return;
    }

    const recalc = () => {
      const container = containerRef.current;
      const measure = measureRef.current;
      if (!container || !measure) {
        setVisibleCount(macros.length);
        return;
      }

      const chipEls = measure.querySelectorAll<HTMLElement>("[data-macro-measure]");
      if (!chipEls.length) {
        setVisibleCount(macros.length);
        return;
      }

      const widths = Array.from(chipEls).map((el) => el.offsetWidth);
      const totalWidth =
        widths.reduce((sum, w) => sum + w, 0) + CHIP_GAP * Math.max(0, widths.length - 1);
      const rowWidth = rowRef.current?.clientWidth ?? container.clientWidth;
      const moreBtn = measure.querySelector<HTMLElement>(".tk-macros__chip--more");
      const moreWidth = (moreBtn?.offsetWidth ?? 56) + CHIP_GAP;

      if (totalWidth <= rowWidth) {
        setVisibleCount(macros.length);
        return;
      }

      let used = 0;
      let count = 0;

      for (let i = 0; i < widths.length; i++) {
        const remaining = widths.length - i - 1;
        const reserve = remaining > 0 ? moreWidth : 0;
        const next = used + (count > 0 ? CHIP_GAP : 0) + widths[i];
        if (next + reserve > rowWidth) break;
        used = next;
        count += 1;
      }

      setVisibleCount(Math.max(MIN_VISIBLE, count));
    };

    recalc();
    const ro = new ResizeObserver(recalc);
    if (containerRef.current) ro.observe(containerRef.current);
    if (rowRef.current) ro.observe(rowRef.current);
    return () => ro.disconnect();
  }, [macros]);

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (containerRef.current?.contains(t)) return;
      setMenuOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  const unreadBadge =
    subscriberUnreadCount > 0 ? (
      <span className="tk-macros__mode-badge" aria-label={`Новых сообщений: ${subscriberUnreadCount}`}>
        {subscriberUnreadCount > 99 ? "99+" : subscriberUnreadCount}
      </span>
    ) : null;

  const modeSwitchDisabled = hideMacros ? false : disabled;

  if (chatPanel === "comments" && onChatPanelChange) {
    return (
      <div className="tk-macros">
        <span className="tk-macros__label">Служебные комментарии</span>
        <div className="tk-macros__bar">
          <div className="tk-macros__mode">
            <button
              type="button"
              className="tk-macros__chip tk-macros__chip--mode tk-macros__chip--mode-active"
              disabled={modeSwitchDisabled}
              onClick={() => onChatPanelChange("subscriber")}
            >
              Чат абонента
              {unreadBadge}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (hideMacros && onChatPanelChange) {
    return (
      <div className="tk-macros">
        <div className="tk-macros__bar">
          <div className="tk-macros__mode">
            <button
              type="button"
              className="tk-macros__chip tk-macros__chip--mode"
              onClick={() => onChatPanelChange("comments")}
            >
              Комментарии
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!macros.length && !onChatPanelChange) return null;

  const visible = macros.slice(0, visibleCount);
  const overflow = macros.slice(visibleCount);

  function pick(m: HelpdeskMacro) {
    if (disabled) return;
    onPick(m);
    setMenuOpen(false);
  }

  const modeToggle =
    chatPanel && onChatPanelChange ? (
      <div className="tk-macros__mode">
        {chatPanel === "subscriber" ? (
          <button
            type="button"
            className="tk-macros__chip tk-macros__chip--mode"
            disabled={modeSwitchDisabled}
            onClick={() => onChatPanelChange("comments")}
          >
            Комментарии
          </button>
        ) : (
          <button
            type="button"
            className="tk-macros__chip tk-macros__chip--mode tk-macros__chip--mode-active"
            disabled={modeSwitchDisabled}
            onClick={() => onChatPanelChange("subscriber")}
          >
            Чат абонента
          </button>
        )}
      </div>
    ) : null;

  return (
    <div className="tk-macros" ref={containerRef}>
      <span className="tk-macros__label">Быстрые ответы:</span>
      <div className="tk-macros__bar">
        <div className="tk-macros__row" ref={rowRef}>
          {visible.map((m) => (
            <button
              key={m.id}
              type="button"
              className="tk-macros__chip"
              disabled={disabled}
              title={m.message_text.trim() || m.name}
              onClick={() => pick(m)}
            >
              {m.name}
            </button>
          ))}
          {overflow.length ? (
            <div className="tk-macros__more-wrap">
              <button
                type="button"
                className={`tk-macros__chip tk-macros__chip--more${menuOpen ? " tk-macros__chip--open" : ""}`}
                disabled={disabled}
                aria-expanded={menuOpen}
                aria-haspopup="menu"
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpen((v) => !v);
                }}
              >
                Ещё ▾
              </button>
              {menuOpen ? (
                <div className="tk-macros__menu" role="menu">
                  {overflow.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      className="tk-macros__menu-item"
                      role="menuitem"
                      title={m.message_text.trim() || m.name}
                      onClick={() => pick(m)}
                    >
                      {m.name}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
        {modeToggle}
      </div>
      <div className="tk-macros__measure" ref={measureRef} aria-hidden>
        {macros.map((m) => (
          <button key={m.id} type="button" className="tk-macros__chip" data-macro-measure disabled>
            {m.name}
          </button>
        ))}
        <button type="button" className="tk-macros__chip tk-macros__chip--more" disabled>
          Ещё ▾
        </button>
      </div>
    </div>
  );
}
