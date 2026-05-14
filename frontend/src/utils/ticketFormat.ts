/** Форматирование для списка тикетов (локальное время браузера). */

export function formatTicketUpdatedLocal(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const s = d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  return s.replace(",", "").replace(/\s+/g, " ").trim();
}

/** Длительность с момента создания: «N дн. HH:MM» или «HH:MM», если меньше суток. */
export function formatWorkDurationSince(iso: string, nowMs: number = Date.now()): string {
  const start = new Date(iso).getTime();
  if (Number.isNaN(start)) return "—";
  const totalMin = Math.max(0, Math.floor((nowMs - start) / 60_000));
  const days = Math.floor(totalMin / (24 * 60));
  const rem = totalMin % (24 * 60);
  const h = Math.floor(rem / 60);
  const m = rem % 60;
  const hh = String(h).padStart(2, "0");
  const mm = String(m).padStart(2, "0");
  if (days >= 1) return `${days} дн. ${hh}:${mm}`;
  return `${hh}:${mm}`;
}
