const LOWERS = "abcdefghijklmnopqrstuvwxyz";
const UPPERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const DIGITS = "0123456789";
const POOL = LOWERS + UPPERS + DIGITS;

export function generateOperatorPassword(length = 10): string {
  const pick = (s: string) => s[Math.floor(Math.random() * s.length)]!;
  const chars = [pick(LOWERS), pick(UPPERS), pick(DIGITS)];
  for (let i = 3; i < length; i += 1) {
    chars.push(pick(POOL));
  }
  for (let i = chars.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [chars[i], chars[j]] = [chars[j]!, chars[i]!];
  }
  return chars.join("");
}

export const CYRILLIC_FULL_NAME_RE = /^[А-ЯЁа-яё]+(?:[ -][А-ЯЁа-яё]+)+$/;

export function validateCyrillicFullName(value: string): string | null {
  const name = value.trim();
  if (!name) return "Укажите ФИО";
  if (!CYRILLIC_FULL_NAME_RE.test(name)) {
    return "ФИО: только русские буквы, минимум имя и фамилия";
  }
  return null;
}
