export type AppTheme = "light" | "dark" | "comfort";

/** 1. Солнце с тучкой (основная) → 2. Солнце → 3. Тёмная */
export const THEME_ORDER: readonly AppTheme[] = ["comfort", "light", "dark"];

export function parseStoredTheme(raw: string | null): AppTheme {
  if (raw === "light" || raw === "dark") return raw;
  return "comfort";
}

export function nextTheme(current: AppTheme): AppTheme {
  const idx = THEME_ORDER.indexOf(current);
  return THEME_ORDER[(idx + 1) % THEME_ORDER.length];
}

/** Подсказка кнопки: какая тема включится по клику. */
export function themeToggleHint(current: AppTheme): string {
  const next = nextTheme(current);
  if (next === "dark") return "Включить тёмную тему";
  if (next === "light") return "Включить светлую тему";
  return "Включить тему «солнце с тучкой»";
}

export function themeCurrentLabel(current: AppTheme): string {
  if (current === "dark") return "Тёмная тема";
  if (current === "light") return "Светлая тема";
  return "Солнце с тучкой";
}
