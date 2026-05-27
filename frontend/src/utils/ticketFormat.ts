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

/** Длительность с момента создания: «N мес. D дн HH:MM», пропуская пустые части. */
export function formatWorkDurationSince(iso: string, nowMs: number = Date.now()): string {
  const start = new Date(iso).getTime();
  if (Number.isNaN(start)) return "—";
  const totalMin = Math.max(0, Math.floor((nowMs - start) / 60_000));
  const daysTotal = Math.floor(totalMin / (24 * 60));
  const rem = totalMin % (24 * 60);
  const h = Math.floor(rem / 60);
  const m = rem % 60;
  const hh = String(h).padStart(2, "0");
  const mm = String(m).padStart(2, "0");
  const months = Math.floor(daysTotal / 30);
  const days = daysTotal % 30;
  const parts: string[] = [];
  if (months > 0) parts.push(`${months} мес.`);
  if (days > 0) parts.push(`${days} дн`);
  parts.push(`${hh}:${mm}`);
  return parts.join(" ");
}
