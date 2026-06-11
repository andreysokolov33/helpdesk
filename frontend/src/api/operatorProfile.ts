import type { AuthMe } from "@/api/auth";

export const PROFILE_MIN_YEAR = 2026;

export type OperatorTicketMonthStats = {
  year: number;
  month: number;
  date_from: string;
  date_to: string;
  open_count: number;
  closed_count: number;
};

export async function fetchOperatorTicketStats(
  year: number,
  month: number,
): Promise<OperatorTicketMonthStats> {
  const sp = new URLSearchParams({
    year: String(year),
    month: String(month),
  });
  const res = await fetch(`/api/v1/helpdesk/operators/me/ticket-stats?${sp}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<OperatorTicketMonthStats>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as OperatorTicketMonthStats;
}

const MONTH_NAMES = [
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
] as const;

export function profileMonthName(month: number): string {
  return MONTH_NAMES[month - 1] ?? String(month);
}

export function getProfileYearOptions(now = new Date()): number[] {
  const currentYear = now.getFullYear();
  const years: number[] = [];
  for (let y = currentYear; y >= PROFILE_MIN_YEAR; y--) {
    years.push(y);
  }
  return years;
}

/** Месяцы для выбора: в текущем году — с января по текущий; в прошлых годах — все 12. */
export function getProfileMonthOptions(year: number, now = new Date()): number[] {
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  if (year < PROFILE_MIN_YEAR || year > currentYear) return [];
  if (year < currentYear) {
    return Array.from({ length: 12 }, (_, i) => i + 1);
  }
  // Текущий год: с 1 по текущий месяц (будущие недоступны)
  return Array.from({ length: currentMonth }, (_, i) => i + 1);
}

export function clampProfileMonth(year: number, month: number, now = new Date()): number {
  const options = getProfileMonthOptions(year, now);
  if (options.length === 0) return 1;
  if (options.includes(month)) return month;
  return options[options.length - 1];
}

export function getDefaultProfilePeriod(now = new Date()): { year: number; month: number } {
  const years = getProfileYearOptions(now);
  const year = years[0] ?? PROFILE_MIN_YEAR;
  const months = getProfileMonthOptions(year, now);
  if (months.length === 0) {
    const prevYear = year - 1;
    if (prevYear >= PROFILE_MIN_YEAR) {
      return { year: prevYear, month: 12 };
    }
    return { year: PROFILE_MIN_YEAR, month: 1 };
  }
  return { year, month: months[months.length - 1] };
}

export function ticketsListUrl(opts: {
  closed: boolean;
  dateFrom: string;
  dateTo: string;
  assignedTo?: number;
}): string {
  const sp = new URLSearchParams({
    date_from: opts.dateFrom,
    date_to: opts.dateTo,
  });
  if (opts.closed) sp.set("closed", "true");
  if (opts.assignedTo != null) sp.set("assigned_to", String(opts.assignedTo));
  return `/tickets?${sp.toString()}`;
}

export type { AuthMe };
