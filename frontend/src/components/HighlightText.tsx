type Props = {
  text: string;
  query: string;
  className?: string;
};

type Part = { value: string; match: boolean };

/** Индексы символов в src, которые нужно подсветить. */
function collectHighlightIndices(src: string, query: string): Set<number> {
  const indices = new Set<number>();
  const q = query.trim();
  if (!q || !src) return indices;

  const lower = src.toLowerCase();
  const needle = q.toLowerCase();
  let i = 0;
  while (i < src.length) {
    const idx = lower.indexOf(needle, i);
    if (idx === -1) break;
    for (let j = idx; j < idx + needle.length; j++) indices.add(j);
    i = idx + needle.length;
  }
  if (indices.size > 0) return indices;

  const qDigits = q.replace(/\D/g, "");
  if (qDigits.length < 2) return indices;

  const map: number[] = [];
  let digits = "";
  for (let j = 0; j < src.length; j++) {
    if (/\d/.test(src[j])) {
      digits += src[j];
      map.push(j);
    }
  }
  let d = 0;
  while (d <= digits.length - qDigits.length) {
    const idx = digits.indexOf(qDigits, d);
    if (idx === -1) break;
    for (let k = idx; k < idx + qDigits.length; k++) indices.add(map[k]);
    d = idx + 1;
  }
  return indices;
}

function partsFromIndices(src: string, indices: Set<number>): Part[] {
  if (!indices.size) return [{ value: src, match: false }];
  const parts: Part[] = [];
  let i = 0;
  while (i < src.length) {
    const match = indices.has(i);
    let j = i + 1;
    while (j < src.length && indices.has(j) === match) j++;
    parts.push({ value: src.slice(i, j), match });
    i = j;
  }
  return parts;
}

/**
 * Подсвечивает вхождения query в text.
 * Сначала — буквальное совпадение; иначе — по цифрам через пробелы
 * (серия и номер паспорта, форматированный телефон).
 */
export default function HighlightText({ text, query, className }: Props) {
  const src = text || "";
  const q = query.trim();
  if (!src || !q) {
    return <span className={className}>{src || "—"}</span>;
  }

  const parts = partsFromIndices(src, collectHighlightIndices(src, q));

  return (
    <span className={className}>
      {parts.map((p, n) =>
        p.match ? (
          <mark key={n} className="sr-mark">
            {p.value}
          </mark>
        ) : (
          <span key={n}>{p.value}</span>
        ),
      )}
    </span>
  );
}
