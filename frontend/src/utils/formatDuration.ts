/** Форматирование длительности в секундах для статистики. */
export function formatDurationSec(sec: number | null | undefined): string {
  if (sec == null || !Number.isFinite(sec) || sec < 0) return "—";
  const total = Math.round(sec);
  if (total < 60) return `${total} с`;
  const m = Math.floor(total / 60);
  const s = total % 60;
  if (m < 60) return s > 0 ? `${m}.${Math.round((s / 60) * 10)}м` : `${m}м`;
  const h = Math.floor(m / 60);
  const rm = m % 60;
  if (h < 24) return rm > 0 ? `${h}ч ${rm}м` : `${h}ч`;
  const d = Math.floor(h / 24);
  const rh = h % 24;
  return rh > 0 ? `${d} д ${rh}ч` : `${d} д`;
}

export function formatRating(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toFixed(1);
}

export function isoDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** С 1-го по последний день текущего месяца. */
export function currentMonthPeriod(): { from: string; to: string } {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  const to = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { from: isoDateLocal(from), to: isoDateLocal(to) };
}

/** Последние N календарных дней, включая сегодня. */
export function lastDaysPeriod(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - (days - 1));
  return { from: isoDateLocal(from), to: isoDateLocal(to) };
}

export function defaultStatsPeriod(): { from: string; to: string } {
  return currentMonthPeriod();
}

/** С 1 января по 31 декабря текущего года. */
export function currentYearPeriod(): { from: string; to: string } {
  const now = new Date();
  const from = new Date(now.getFullYear(), 0, 1);
  const to = new Date(now.getFullYear(), 11, 31);
  return { from: isoDateLocal(from), to: isoDateLocal(to) };
}

export type StatsPeriodPreset = "month" | "7d" | "30d" | "year" | "custom";

export function statsPeriodForPreset(preset: Exclude<StatsPeriodPreset, "custom">): { from: string; to: string } {
  if (preset === "month") return currentMonthPeriod();
  if (preset === "7d") return lastDaysPeriod(7);
  if (preset === "30d") return lastDaysPeriod(30);
  return currentYearPeriod();
}

export function detectStatsPeriodPreset(from: string, to: string): StatsPeriodPreset {
  const month = currentMonthPeriod();
  const d7 = lastDaysPeriod(7);
  const d30 = lastDaysPeriod(30);
  const year = currentYearPeriod();
  if (from === month.from && to === month.to) return "month";
  if (from === d7.from && to === d7.to) return "7d";
  if (from === d30.from && to === d30.to) return "30d";
  if (from === year.from && to === year.to) return "year";
  return "custom";
}

export function todayYmd(): string {
  return isoDateLocal(new Date());
}
