export type HelpdeskMacro = {
  id: number;
  name: string;
  message_text: string;
  sort_order: number;
};

export async function fetchHelpdeskMacros(): Promise<HelpdeskMacro[]> {
  const res = await fetch("/api/v1/helpdesk/tracker/macros", { credentials: "include" });
  const data = (await res.json().catch(() => ({}))) as { items?: HelpdeskMacro[]; detail?: string };
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return Array.isArray(data.items) ? data.items : [];
}

/** Plain text / переносы → HTML для RichEditor. */
export function macroTextToEditorHtml(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "";
  if (/<[a-z][\s\S]*?>/i.test(trimmed)) return trimmed;
  const escape = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return trimmed
    .split(/\n{2,}/)
    .map((block) => `<p>${escape(block).replace(/\n/g, "<br>")}</p>`)
    .join("");
}
