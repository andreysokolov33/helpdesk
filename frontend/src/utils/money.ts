/** Сумма в ₽: тысячи с узким пробелом, без копеек если целое. */
export function fmtMoneyRu(n: number): string {
  const rounded = Math.round(n * 100) / 100;
  if (Math.abs(rounded - Math.round(rounded)) < 1e-9) {
    const body = Math.round(rounded)
      .toString()
      .replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f");
    return `${body}\u202f₽`;
  }
  const whole = Math.trunc(rounded);
  const kop = Math.round((rounded - whole) * 100);
  const body = whole.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f");
  return `${body},${kop.toString().padStart(2, "0")}\u202f₽`;
}
