type Props = { filename?: string | null; ext?: string | null };

const TYPES: Record<string, { label: string; bg: string }> = {
  pdf:  { label: "PDF",  bg: "#dc2626" },
  doc:  { label: "DOC",  bg: "#2563eb" },
  docx: { label: "DOC",  bg: "#2563eb" },
  xls:  { label: "XLS",  bg: "#16a34a" },
  xlsx: { label: "XLS",  bg: "#16a34a" },
  csv:  { label: "CSV",  bg: "#0891b2" },
};

export function resolveFileExt(filename?: string | null, ext?: string | null): string {
  if (ext) return ext.toLowerCase().replace(/^\./, "");
  if (!filename) return "";
  const dot = filename.lastIndexOf(".");
  return dot >= 0 ? filename.slice(dot + 1).toLowerCase() : "";
}

export function truncateFilename(name: string, maxLen = 28): string {
  if (name.length <= maxLen) return name;
  const dot = name.lastIndexOf(".");
  if (dot > 0 && name.length - dot <= 6) {
    const ext = name.slice(dot);
    const stem = name.slice(0, dot);
    const keep = maxLen - ext.length - 1;
    return `${stem.slice(0, Math.max(keep, 4))}…${ext}`;
  }
  return `${name.slice(0, maxLen - 1)}…`;
}

export default function FileBadge({ filename, ext }: Props) {
  const resolved = resolveFileExt(filename, ext);
  const info = TYPES[resolved] ?? { label: resolved.toUpperCase().slice(0, 4) || "FILE", bg: "#6b7280" };
  return (
    <span
      className="tk-file-badge"
      style={{ background: info.bg }}
      aria-hidden
    >
      {info.label}
    </span>
  );
}
