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
