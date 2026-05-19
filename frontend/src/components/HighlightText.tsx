type Props = {
  text: string;
  query: string;
  className?: string;
};

/** Подсвечивает все вхождения query в text (регистронезависимо). */
export default function HighlightText({ text, query, className }: Props) {
  const src = text || "";
  const q = query.trim();
  if (!src || !q) {
    return <span className={className}>{src || "—"}</span>;
  }

  const lower = src.toLowerCase();
  const needle = q.toLowerCase();
  const parts: { value: string; match: boolean }[] = [];
  let i = 0;

  while (i < src.length) {
    const idx = lower.indexOf(needle, i);
    if (idx === -1) {
      parts.push({ value: src.slice(i), match: false });
      break;
    }
    if (idx > i) parts.push({ value: src.slice(i, idx), match: false });
    parts.push({ value: src.slice(idx, idx + needle.length), match: true });
    i = idx + needle.length;
  }

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
