import type { TicketRow } from "@/data/mockCc";

export type TrackerTicketListItem = {
  id: number;
  title: string;
  object_type: string;
  status: string;
  status_label: string;
  priority: string | null;
  priority_label: string | null;
  support_line: number;
  support_line_label: string;
  source: string | null;
  source_label: string;
  category_label: string | null;
  user_id: number | null;
  subscriber_profile_user_id: number | null;
  subscriber_is_juridical: number;
  subscriber_name: string | null;
  subscriber_login: string | null;
  assignee_name: string | null;
  assignee_role: string | null;
  assignee_is_viewer: boolean;
  has_unread: boolean;
  communication_state: "needs_reply" | "awaiting_subscriber" | null;
  communication_label: string | null;
  date_of_create: string;
  updated_at: string | null;
};

export type TrackerTicketListResponse = {
  total: number;
  page: number;
  per_page: number;
  items: TrackerTicketListItem[];
};

export async function fetchOpenTrackerTickets(params: {
  page: number;
  per_page: number;
  closed?: boolean;
}): Promise<TrackerTicketListResponse> {
  const sp = new URLSearchParams({
    page: String(params.page),
    per_page: String(params.per_page),
  });
  if (params.closed) sp.set("closed", "true");
  const res = await fetch(`/api/v1/helpdesk/tracker/list?${sp.toString()}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<TrackerTicketListResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as TrackerTicketListResponse;
}

const _WAIT = new Set([
  "waiting_client",
  "waiting_technician",
  "waiting_parts",
  "waiting_logistics",
  "waiting_cs",
  "cc_handover",
  "no_technician",
]);

export type RegisterCallPayload = {
  body: string;
  subscriber_unknown: boolean;
  user_id: number | null;
  caller_name?: string | null;
  station_id?: number | null;
  hotspot_id?: number | null;
};

export type RegisterCallResponse = { id: number };

export async function registerCall(payload: RegisterCallPayload): Promise<RegisterCallResponse> {
  const res = await fetch("/api/v1/helpdesk/tracker/register-call", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<RegisterCallResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  if (data.id == null) throw new Error("Некорректный ответ сервера");
  return { id: data.id };
}

export function trackerApiRowToTicketRow(row: TrackerTicketListItem): TicketRow {
  let status: TicketRow["status"] = "work";
  if (row.status === "pending" || row.status === "open") status = "new";
  else if (_WAIT.has(row.status)) status = "wait";

  let dot: TicketRow["dot"] = "i2";
  if (row.communication_state === "needs_reply" || row.has_unread) dot = "red";
  else if (row.communication_state === "awaiting_subscriber") dot = "wn";
  else if (_WAIT.has(row.status)) dot = "wn";

  const t = row.updated_at || row.date_of_create;
  const time = new Date(t).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  return {
    id: row.id,
    name: row.subscriber_name || row.subscriber_login || (row.user_id != null ? `Абонент #${row.user_id}` : `Тикет #${row.id}`),
    topic: row.title,
    status,
    time,
    dot,
  };
}
