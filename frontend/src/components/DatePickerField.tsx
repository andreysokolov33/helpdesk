import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

const WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"];
const MONTHS = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
];

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function toYmd(d: Date) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function parseYmd(s: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const [y, m, d] = s.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d ? dt : null;
}

function formatDisplay(ymd: string) {
  const d = parseYmd(ymd);
  if (!d) return "";
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

type Props = {
  value: string;
  onChange: (value: string) => void;
  minDate?: string;
  id?: string;
  placeholder?: string;
};

export default function DatePickerField({
  value,
  onChange,
  minDate,
  id,
  placeholder = "Выберите дату",
}: Props) {
  const uid = useId();
  const wrapRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [view, setView] = useState(() => parseYmd(value) ?? new Date());
  const [pos, setPos] = useState({ top: 0, left: 0, width: 280 });

  useEffect(() => {
    if (value) {
      const p = parseYmd(value);
      if (p) setView(new Date(p.getFullYear(), p.getMonth(), 1));
    }
  }, [value]);

  useEffect(() => {
    if (!open) return;
    const sync = () => {
      const el = wrapRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const calH = 320;
      const gap = 6;
      const below = r.bottom + gap;
      const above = r.top - gap - calH;
      const top = below + calH > window.innerHeight - 8 && above > 8 ? above : below;
      const left = Math.min(Math.max(8, r.left), window.innerWidth - 288);
      setPos({ top, left, width: Math.min(280, window.innerWidth - 16) });
    };
    sync();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (wrapRef.current?.contains(t)) return;
      const cal = document.getElementById(`dp-cal-${uid}`);
      if (cal?.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, uid]);

  const year = view.getFullYear();
  const month = view.getMonth();
  const todayYmd = toYmd(new Date());
  const min = minDate && parseYmd(minDate) ? minDate : undefined;

  const first = new Date(year, month, 1);
  const startPad = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: { ymd: string | null; day: number }[] = [];
  for (let i = 0; i < startPad; i++) cells.push({ ymd: null, day: 0 });
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ ymd: `${year}-${pad2(month + 1)}-${pad2(d)}`, day: d });
  }

  function pick(ymd: string) {
    if (min && ymd < min) return;
    onChange(ymd);
    setOpen(false);
  }

  const calendar = open ? (
    <div
      id={`dp-cal-${uid}`}
      className="up-dp-cal"
      style={{ top: pos.top, left: pos.left, width: pos.width }}
      role="dialog"
      aria-label="Календарь"
    >
      <div className="up-dp-cal-head">
        <button
          type="button"
          className="up-dp-nav"
          aria-label="Предыдущий месяц"
          onClick={() => setView(new Date(year, month - 1, 1))}
        >
          ‹
        </button>
        <div className="up-dp-cal-title">
          {MONTHS[month]} {year}
        </div>
        <button
          type="button"
          className="up-dp-nav"
          aria-label="Следующий месяц"
          onClick={() => setView(new Date(year, month + 1, 1))}
        >
          ›
        </button>
      </div>
      <div className="up-dp-weekdays">
        {WEEKDAYS.map((w, i) => (
          <span key={w} className={i >= 5 ? "up-dp-wd up-dp-wd--off" : "up-dp-wd"}>
            {w}
          </span>
        ))}
      </div>
      <div className="up-dp-grid">
        {cells.map((c, i) =>
          c.ymd ? (
            <button
              key={c.ymd + i}
              type="button"
              className={[
                "up-dp-day",
                c.ymd === value ? "selected" : "",
                c.ymd === todayYmd ? "today" : "",
                min && c.ymd < min ? "disabled" : "",
                [0, 6].includes((startPad + c.day - 1) % 7) ? "weekend" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              disabled={!!(min && c.ymd < min)}
              onClick={() => pick(c.ymd)}
            >
              {c.day}
            </button>
          ) : (
            <span key={`e-${i}`} className="up-dp-day up-dp-day--empty" aria-hidden />
          ),
        )}
      </div>
      <div className="up-dp-cal-foot">
        <button type="button" className="up-dp-foot-btn" onClick={() => onChange("")}>
          Очистить
        </button>
        <button
          type="button"
          className="up-dp-foot-btn up-dp-foot-btn--pri"
          onClick={() => pick(todayYmd)}
        >
          Сегодня
        </button>
      </div>
    </div>
  ) : null;

  return (
    <div className="up-dp-wrap" ref={wrapRef}>
      <button
        id={id}
        type="button"
        className={`up-dp-trigger${open ? " open" : ""}${value ? " filled" : ""}`}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((o) => !o)}
      >
        <span className={value ? "up-dp-trigger-val" : "up-dp-trigger-ph"}>
          {value ? formatDisplay(value) : placeholder}
        </span>
        <span className="up-dp-trigger-ico" aria-hidden>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" />
            <path d="M16 2v4M8 2v4M3 10h18" />
          </svg>
        </span>
      </button>
      {calendar && createPortal(calendar, document.body)}
    </div>
  );
}

/** YYYY-MM-DD → ISO (полночь по локальному времени браузера) */
export function dateYmdToIso(ymd: string): string {
  return new Date(`${ymd}T00:00:00`).toISOString();
}
