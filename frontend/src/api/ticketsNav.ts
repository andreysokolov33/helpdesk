export async function fetchUnreadTicketsCount(): Promise<number> {
  const res = await fetch("/api/v1/helpdesk/tickets/unread_count", {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string; unread_count?: number };
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return typeof data.unread_count === "number" ? data.unread_count : 0;
}
