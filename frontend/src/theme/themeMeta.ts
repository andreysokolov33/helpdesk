export type AppTheme = "light" | "dark" | "comfort";

/**
 * Цикл переключения тем (кнопка в шапке).
 * «light» (чистое солнце) спрятана — не удалять из типа/CSS, только из порядка.
 */
export const THEME_ORDER: readonly AppTheme[] = [
  "comfort", // основная; в UI — иконка солнышка
  // "light",
  "dark",
];

export function parseStoredTheme(raw: string | null): AppTheme {
  if (raw === "dark") return "dark";
  // Спрятанная светлая тема: при старом значении в localStorage → основная
  // if (raw === "light") return "light";
  if (raw === "light") return "comfort";
  return "comfort";
}

export function nextTheme(current: AppTheme): AppTheme {
  const idx = THEME_ORDER.indexOf(current);
  const safeIdx = idx >= 0 ? idx : 0;
  return THEME_ORDER[(safeIdx + 1) % THEME_ORDER.length];
}

/** Подсказка кнопки: какая тема включится по клику. */
export function themeToggleHint(current: AppTheme): string {
  const next = nextTheme(current);
  if (next === "dark") return "Включить тёмную тему";
  // if (next === "light") return "Включить светлую тему";
  return "Включить светлую тему";
}

export function themeCurrentLabel(current: AppTheme): string {
  if (current === "dark") return "Тёмная тема";
  // if (current === "light") return "Светлая тема";
  return "Светлая тема";
}
