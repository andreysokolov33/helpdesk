/** Лейблы тикетов: категория, статус, линия ТП (профиль абонента, списки). */

const CATEGORY_THEMES = ["finance", "network", "equipment", "traffic", "other"] as const;
export type TicketCategoryTheme = (typeof CATEGORY_THEMES)[number];

export function categoryBadgeClass(
  theme: string | null | undefined,
  categoryName: string | null | undefined,
): TicketCategoryTheme | "empty" {
  if (theme && (CATEGORY_THEMES as readonly string[]).includes(theme)) {
    return theme as TicketCategoryTheme;
  }
  if (!categoryName?.trim()) return "empty";
  let h = 0;
  for (let i = 0; i < categoryName.length; i++) {
    h = (Math.imul(31, h) + categoryName.charCodeAt(i)) | 0;
  }
  return CATEGORY_THEMES[Math.abs(h) % CATEGORY_THEMES.length];
}

export function queueLineBadgeClass(line: string): "1" | "2" | "3" | "o" {
  if (line === "cs") return "1";
  if (line === "engineers") return "2";
  if (line === "partner") return "3";
  return "o";
}

export function queueLineShortLabel(line: string, legacySupportLine?: number): string {
  if (line === "cs") return "КС";
  if (line === "engineers") return "Инженеры";
  if (line === "partner") return "Партнёр";
  if (legacySupportLine === 2) return "Инженеры";
  if (legacySupportLine === 3) return "Партнёр";
  return "КС";
}

export function supportLineBadgeClass(line: number): "1" | "2" | "3" | "o" {
  if (line === 1 || line === 2 || line === 3) return String(line) as "1" | "2" | "3";
  return "o";
}

export function supportLineLabel(line: number, label?: string | null): string {
  if (label?.trim()) return label;
  if (line === 1) return "Контактный сервис";
  if (line === 2) return "Инженеры";
  if (line === 3) return "Партнёр";
  return String(line);
}

/** Карточка тикета: 1 → КС, иначе → Инженеры. */
export function ticketSupportLineShortLabel(line: number): string {
  return line === 1 ? "КС" : "Инженеры";
}

export function ticketSupportLineBadgeClass(line: number): "1" | "2" {
  return line === 1 ? "1" : "2";
}

const PRIORITY_BADGE_KEYS = ["low", "middle", "high", "critical"] as const;
export type PriorityBadgeKey = (typeof PRIORITY_BADGE_KEYS)[number];

export function priorityBadgeClass(priority: string | null | undefined): PriorityBadgeKey {
  const p = (priority || "middle").toLowerCase();
  if ((PRIORITY_BADGE_KEYS as readonly string[]).includes(p)) {
    return p as PriorityBadgeKey;
  }
  return "middle";
}

const SOURCE_BADGE_KEYS = [
  "lk",
  "call_center",
  "abs",
  "partner",
  "tech",
  "ks",
  "chat",
  "technician",
  "internal",
] as const;
export type SourceBadgeKey = (typeof SOURCE_BADGE_KEYS)[number] | "other";

export function sourceBadgeClass(source: string | null | undefined): SourceBadgeKey {
  const s = (source || "call_center").toLowerCase();
  if ((SOURCE_BADGE_KEYS as readonly string[]).includes(s)) {
    return s as SourceBadgeKey;
  }
  return "other";
}

/** Переписка ЛК (user_mail), быстрые ответы и комментарии при передаче инженерам. */
export function isLkTicketSource(source: string | null | undefined): boolean {
  return (source ?? "").trim().toLowerCase() === "lk";
}
