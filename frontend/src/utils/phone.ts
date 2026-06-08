/** Цифры из строки телефона (для копирования и валидации). */
export function phoneDigits(raw: string | null | undefined): string {
  if (!raw) return "";
  return raw.replace(/\D/g, "");
}

/** Полный RU-номер: +7 и ровно 10 цифр (12 символов). */
export const RU_PHONE_COMPLETE_RE = /^\+7\d{10}$/;

/**
 * Маска ввода: +7XXXXXXXXXX, не больше 10 цифр после +7.
 * 8… и 7… в начале нормализуются к +7….
 */
export function maskRuPhoneInput(raw: string): string {
  let digits = phoneDigits(raw);
  if (!digits) return "+7";
  if (digits.startsWith("8")) digits = `7${digits.slice(1)}`;
  if (!digits.startsWith("7")) digits = `7${digits}`;
  digits = digits.slice(0, 11);
  if (digits.length <= 1) return "+7";
  return `+7${digits.slice(1)}`;
}

export function isCompleteRuPhone(raw: string | null | undefined): boolean {
  return RU_PHONE_COMPLETE_RE.test((raw ?? "").trim());
}

/** Нормализованный номер для API: +7XXXXXXXXXX. */
export function normalizeRuPhone(raw: string): string | null {
  const masked = maskRuPhoneInput(raw);
  return isCompleteRuPhone(masked) ? masked : null;
}

/**
 * Форматирование RU-телефонов: +7 (XXX) XXX-XX-XX.
 * Если распознать не удалось — исходная строка.
 */
export function formatPhoneDisplay(raw: string | null | undefined): string {
  if (!raw?.trim()) return "—";
  const src = raw.trim();
  let d = phoneDigits(src);
  if (!d) return src;

  if (d.length === 11 && (d.startsWith("7") || d.startsWith("8"))) {
    d = d.startsWith("8") ? `7${d.slice(1)}` : d;
    return `+7 (${d.slice(1, 4)}) ${d.slice(4, 7)}-${d.slice(7, 9)}-${d.slice(9, 11)}`;
  }
  if (d.length === 10) {
    return `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8, 10)}`;
  }
  return src;
}

export async function copyPhone(raw: string | null | undefined): Promise<void> {
  const d = phoneDigits(raw);
  const text = d || (raw ?? "");
  if (!text) return;
  await navigator.clipboard.writeText(text);
}
