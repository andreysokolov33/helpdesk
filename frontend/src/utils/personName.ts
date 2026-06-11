/** «Иванов Иван Иванович» → «Иванов И.И.» */
export function formatStaffNameShort(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "—";
  if (parts.length === 1) return parts[0];
  const surname = parts[0];
  const initials = parts
    .slice(1)
    .map((part) => {
      const ch = part[0];
      return ch ? `${ch.toUpperCase()}.` : "";
    })
    .filter(Boolean)
    .join("");
  return initials ? `${surname} ${initials}` : surname;
}
