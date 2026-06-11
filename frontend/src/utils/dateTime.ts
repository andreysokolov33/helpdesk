/**
 * Парсинг дат с API (PostgreSQL timestamptz → ISO).
 * Без суффикса зоны трактуем как UTC, отображение — в локали браузера.
 */

function normalizeIsoString(iso: string): string {
  let s = iso.trim();
  if (/^\d{4}-\d{2}-\d{2} /.test(s)) {
    s = s.replace(" ", "T");
  }
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) {
    s = s.includes("T") ? s : `${s}T00:00:00`;
    if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) {
      s = `${s}Z`;
    }
  }
  return s;
}

export function parseApiDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(normalizeIsoString(iso));
  return Number.isNaN(d.getTime()) ? null : d;
}

export type FormatDateTimeOptions = {
  withYear?: boolean;
  withSeconds?: boolean;
  /** IANA-зона; по умолчанию — часовой пояс браузера (администратора/оператора). */
  timeZone?: string;
};

/** Часовой пояс браузера текущего пользователя (например Europe/Moscow). */
export function viewerTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/** Дата/время в часовом поясе пользователя (локаль браузера). */
export function formatDateTimeLocal(
  iso: string | null | undefined,
  opts: FormatDateTimeOptions = {},
): string {
  const d = parseApiDate(iso);
  if (!d) return "";

  const { withYear = false, withSeconds = false, timeZone = viewerTimeZone() } = opts;

  return d
    .toLocaleString("ru-RU", {
      timeZone,
      day: "numeric",
      month: "short",
      ...(withYear ? { year: "numeric" } : {}),
      hour: "2-digit",
      minute: "2-digit",
      ...(withSeconds ? { second: "2-digit" } : {}),
      hour12: false,
    })
    .replace(/\s+/g, " ")
    .trim();
}
