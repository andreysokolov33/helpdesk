export type AppTheme = "light" | "dark" | "comfort";

/** 1. Солнце (основная) → 2. Солнце с тучкой → 3. Тёмная */
export const THEME_ORDER: readonly AppTheme[] = ["light", "comfort", "dark"];

export function parseStoredTheme(raw: string | null): AppTheme {
  if (raw === "dark" || raw === "comfort") return raw;
  return "light";
}

export function nextTheme(current: AppTheme): AppTheme {
  const idx = THEME_ORDER.indexOf(current);
  return THEME_ORDER[(idx + 1) % THEME_ORDER.length];
}

/** Подсказка кнопки: какая тема включится по клику. */
export function themeToggleHint(current: AppTheme): string {
  const next = nextTheme(current);
  if (next === "dark") return "Включить тёмную тему";
  if (next === "comfort") return "Включить тему «солнце с тучкой»";
  return "Включить основную тему";
}

export function themeCurrentLabel(current: AppTheme): string {
  if (current === "dark") return "Тёмная тема";
  if (current === "comfort") return "Солнце с тучкой";
  return "Основная тема";
}
