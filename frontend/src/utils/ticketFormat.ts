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

/** Компактная дата для колонок списка: «11.06. 14:30». */
export function formatTicketListDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const day = d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
  const time = d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${day} ${time}`;
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

/** Длительность между двумя ISO-датами (для закрытых тикетов). */
export function formatWorkDurationBetween(
  startIso: string,
  endIso: string | null | undefined,
  nowMs: number = Date.now(),
): string {
  const end = endIso ? new Date(endIso).getTime() : nowMs;
  const start = new Date(startIso).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return "—";
  const totalMin = Math.max(0, Math.floor((end - start) / 60_000));
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

/** Формат рейтинга «4,2» или «—». */
export function formatRatingAvg(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(1).replace(".", ",");
}

/** Тон подсветки средней оценки: ≤2 красный, >4 зелёный, между — градация. */
export type RatingTone = "none" | "bad" | "poor" | "mid" | "good";

export function ratingAvgTone(value: number | null | undefined): RatingTone {
  if (value == null || Number.isNaN(value)) return "none";
  if (value <= 2) return "bad";
  if (value <= 3) return "poor";
  if (value <= 4) return "mid";
  return "good";
}

export function ratingToneClass(value: number | null | undefined): string {
  const tone = ratingAvgTone(value);
  return tone === "none" ? "" : `ch-stat-pill--tone-${tone}`;
}
