import type { TicketRow } from "@/data/mockCc";
import { formatStaffNameShort } from "@/utils/personName";

export type TrackerQueueLine = "cs" | "engineers" | "partner";
export type TrackerActionBy = "cs" | "engineers" | "partner" | "subscriber" | "external";
export type TrackerChatTurn = "staff" | "subscriber";
export type TrackerListHighlight = "chat" | "ops" | "none";

export type TicketStaffParticipant = {
  id: number;
  label: string;
  role: "support" | "engineer" | "manager" | string;
  is_primary: boolean;
  is_viewer: boolean;
};

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
  queue_line: TrackerQueueLine;
  action_by: TrackerActionBy;
  chat_turn: TrackerChatTurn;
  action_since: string | null;
  list_highlight: TrackerListHighlight;
  source: string | null;
  source_label: string;
  category_label: string | null;
  user_id: number | null;
  subscriber_profile_user_id: number | null;
  subscriber_is_juridical: number;
  subscriber_name: string | null;
  subscriber_login: string | null;
  assignee_label: string | null;
  assignee_role: string | null;
  assignee_is_viewer: boolean;
  assigned_to: number | null;
  has_unread: boolean;
  top_subscriber_rank?: number | null;
  communication_state: "needs_reply" | "awaiting_subscriber" | null;
  communication_label: string | null;
  date_of_create: string;
  updated_at: string | null;
  date_of_close: string | null;
  rating: number | null;
  rating_comment: string | null;
  /** Превью последнего сообщения чата по тикету. */
  last_message_text?: string | null;
};

export type TrackerTicketListStats = {
  avg_rating: number | null;
  avg_rating_mine: number | null;
};

export type TrackerTicketListResponse = {
  total: number;
  page: number;
  per_page: number;
  items: TrackerTicketListItem[];
  stats: TrackerTicketListStats | null;
};

/** Подписи коммуникационного слоя в колонке «Статус». */
export const COMMUNICATION_LABELS = {
  needs_reply: "Нужен ответ",
  awaiting_reply: "Ждём ответа",
} as const;

const TRACKER_CLOSED_STATUSES = new Set([
  "resolved",
  "closed",
  "cancelled",
  "deferred",
  "not_resolved",
]);

export type TicketStatusColumn =
  | { kind: "comm"; state: keyof typeof COMMUNICATION_LABELS; label: string }
  | { kind: "workflow"; status: string; label: string };

/** Тикет требует внимания: непрочитанное или ожидается ответ на линии зрителя. */
export function ticketListNeedsAttention(
  row: Pick<TrackerTicketListItem, "has_unread" | "list_highlight">,
): boolean {
  if (row.has_unread) return true;
  return row.list_highlight === "chat";
}

const _LIST_ROW_MERGE_KEYS: (keyof TrackerTicketListItem)[] = [
  "status",
  "status_label",
  "priority",
  "priority_label",
  "support_line",
  "support_line_label",
  "queue_line",
  "action_by",
  "chat_turn",
  "action_since",
  "list_highlight",
  "assignee_label",
  "assignee_role",
  "assignee_is_viewer",
  "assigned_to",
  "has_unread",
  "top_subscriber_rank",
  "communication_state",
  "communication_label",
  "updated_at",
  "title",
  "category_label",
  "subscriber_name",
  "last_message_text",
];

function trackerListRowEqual(a: TrackerTicketListItem, b: TrackerTicketListItem): boolean {
  if (a.id !== b.id) return false;
  return _LIST_ROW_MERGE_KEYS.every((k) => a[k] === b[k]);
}

/** Сохраняет ссылки на неизменённые строки — меньше перерисовок при поллинге. */
export function mergeTrackerListPage(
  prev: TrackerTicketListItem[],
  next: TrackerTicketListItem[],
): TrackerTicketListItem[] {
  if (prev.length === 0) return next;
  const prevById = new Map(prev.map((r) => [r.id, r]));
  return next.map((row) => {
    const old = prevById.get(row.id);
    if (old && trackerListRowEqual(old, row)) return old;
    return row;
  });
}

/** Колонка «Исполнитель» — только assigned_to. */
export type AssigneePillVariant = "you" | "unassigned" | "support" | "engineer" | "manager";

export type AssigneePillDisplay = {
  label: string;
  variant: AssigneePillVariant;
  title?: string;
};

export type AssigneePillRow = Pick<
  TrackerTicketListItem,
  "assigned_to" | "assignee_label" | "assignee_role" | "assignee_is_viewer"
>;

function assigneePillVariant(role: string | null | undefined): AssigneePillVariant {
  const r = (role || "support").toLowerCase();
  if (r === "engineer") return "engineer";
  if (r === "manager") return "manager";
  return "support";
}

/** Лейбл одного участника (assigned_to или соисполнитель). */
export function staffParticipantPill(p: TicketStaffParticipant): AssigneePillDisplay {
  if (p.is_viewer) {
    return { label: "Вы", variant: "you" };
  }
  const role = (p.role || "support").toLowerCase();
  if (role === "engineer") {
    return { label: "Инженер", variant: "engineer" };
  }
  if (role === "manager") {
    return { label: "Менеджер", variant: "manager" };
  }
  const full = p.label?.trim() || "—";
  const label = full !== "—" ? formatStaffNameShort(full) : full;
  return {
    label,
    variant: "support",
    title: full !== label ? full : undefined,
  };
}

/** Исполнитель: assigned_to; ФИО только для support. */
export function ticketListAssigneePill(row: AssigneePillRow): AssigneePillDisplay {
  if (row.assigned_to == null) {
    return { label: "Нет исполнителя", variant: "unassigned" };
  }
  if (row.assignee_is_viewer) {
    return { label: "Вы", variant: "you" };
  }
  const role = (row.assignee_role || "support").toLowerCase();
  if (role === "engineer") {
    return { label: "Инженер", variant: "engineer" };
  }
  if (role === "manager") {
    return { label: "Менеджер", variant: "manager" };
  }
  const full = row.assignee_label?.trim() || "—";
  const label = full !== "—" ? formatStaffNameShort(full) : full;
  return {
    label,
    variant: assigneePillVariant(role),
    title: full !== label ? full : undefined,
  };
}

/** @deprecated используйте ticketListAssigneePill */
export function ticketListAssigneeLabel(row: AssigneePillRow): string {
  return ticketListAssigneePill(row).label;
}

/** Колонка «Статус» в /tickets (v2 + workflow). */
export function ticketListStatusColumn(
  row: Pick<
    TrackerTicketListItem,
    | "status"
    | "status_label"
    | "source"
    | "chat_turn"
    | "action_by"
    | "communication_state"
    | "list_highlight"
    | "support_line"
  >,
): TicketStatusColumn {
  if (TRACKER_CLOSED_STATUSES.has(row.status)) {
    return { kind: "workflow", status: row.status, label: row.status_label };
  }

  // Открытые: только «Нужен ответ» (линия зрителя) или серый «Ждём ответа»
  if (row.list_highlight === "chat") {
    return {
      kind: "comm",
      state: "needs_reply",
      label: COMMUNICATION_LABELS.needs_reply,
    };
  }

  return {
    kind: "comm",
    state: "awaiting_reply",
    label: COMMUNICATION_LABELS.awaiting_reply,
  };
}

/** @deprecated используйте ticketListStatusColumn */
export function ticketListCommunicationBadge(
  row: Pick<TrackerTicketListItem, "has_unread" | "communication_state" | "communication_label" | "status">,
): { state: keyof typeof COMMUNICATION_LABELS; label: string } | null {
  const col = ticketListStatusColumn(row);
  return col.kind === "comm" ? { state: col.state, label: col.label } : null;
}

export type TrackerTicketListDigest = {
  changed: boolean;
  digest: string;
  total: number;
};

/** Лёгкий поллинг: changed=false — полный /list не вызывать. */
export async function fetchTrackerListDigest(params: {
  page: number;
  per_page: number;
  closed?: boolean;
  q?: string;
  subscriber_q?: string;
  message_q?: string;
  date_from?: string;
  date_to?: string;
  assigned_to?: number;
  digest?: string;
}): Promise<TrackerTicketListDigest> {
  const sp = new URLSearchParams({
    page: String(params.page),
    per_page: String(params.per_page),
  });
  if (params.closed) sp.set("closed", "true");
  const search = params.q?.trim();
  if (search) sp.set("q", search);
  const sub = params.subscriber_q?.trim();
  if (sub) sp.set("subscriber_q", sub);
  const mq = params.message_q?.trim();
  if (mq && mq.length >= 2) sp.set("message_q", mq);
  if (params.date_from) sp.set("date_from", params.date_from);
  if (params.date_to) sp.set("date_to", params.date_to);
  if (params.assigned_to != null) sp.set("assigned_to", String(params.assigned_to));
  if (params.digest) sp.set("digest", params.digest);
  const res = await fetch(`/api/v1/helpdesk/tracker/list/digest?${sp.toString()}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<TrackerTicketListDigest>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as TrackerTicketListDigest;
}

export async function fetchOpenTrackerTickets(params: {
  page: number;
  per_page: number;
  closed?: boolean;
  q?: string;
  subscriber_q?: string;
  message_q?: string;
  date_from?: string;
  date_to?: string;
  assigned_to?: number;
}): Promise<TrackerTicketListResponse> {
  const sp = new URLSearchParams({
    page: String(params.page),
    per_page: String(params.per_page),
  });
  if (params.closed) sp.set("closed", "true");
  const search = params.q?.trim();
  if (search) sp.set("q", search);
  const sub = params.subscriber_q?.trim();
  if (sub) sp.set("subscriber_q", sub);
  const mq = params.message_q?.trim();
  if (mq && mq.length >= 2) sp.set("message_q", mq);
  if (params.date_from) sp.set("date_from", params.date_from);
  if (params.date_to) sp.set("date_to", params.date_to);
  if (params.assigned_to != null) sp.set("assigned_to", String(params.assigned_to));
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

export type CallConnectionKind = "existing" | "new_subscriber" | "new_partner";

export type ConnectionLeadPayload = {
  full_name: string;
  address: string;
  phone: string;
  potential_subscribers?: number | null;
  sees_network?: boolean | null;
  plans_new_station?: boolean | null;
  notes?: string | null;
};

export type RegisterCallPayload = {
  connection_kind: CallConnectionKind;
  body?: string | null;
  user_id?: number | null;
  lead?: ConnectionLeadPayload | null;
  station_id?: number | null;
  hotspot_id?: number | null;
  /** call_center (default) | old_cs — тикет из старого чата /chat */
  source?: "call_center" | "old_cs" | null;
  /** low | middle | high | critical (default middle) */
  priority?: "low" | "middle" | "high" | "critical" | null;
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

export type OpenSubscriberTicketItem = {
  id: number;
  title: string;
  status: string;
  status_label: string;
  date_of_create: string;
  updated_at?: string | null;
};

export type OpenSubscriberTicketsResponse = {
  items: OpenSubscriberTicketItem[];
};

/** Открытые тикеты абонента с указанным source (модалка создания из /chat). */
export async function fetchOpenTicketsForSubscriber(params: {
  user_id: number;
  source?: string;
  limit?: number;
}): Promise<OpenSubscriberTicketsResponse> {
  const sp = new URLSearchParams();
  sp.set("user_id", String(params.user_id));
  if (params.source) sp.set("source", params.source);
  if (params.limit != null) sp.set("limit", String(params.limit));
  const res = await fetch(`/api/v1/helpdesk/tracker/open-for-subscriber?${sp}`, {
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<OpenSubscriberTicketsResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return { items: Array.isArray(data.items) ? data.items : [] };
}

export function trackerApiRowToTicketRow(row: TrackerTicketListItem): TicketRow {
  let status: TicketRow["status"] = "work";
  if (row.status === "pending" || row.status === "open") status = "new";
  else if (_WAIT.has(row.status)) status = "wait";

  let dot: TicketRow["dot"] = "i2";
  if (ticketListNeedsAttention(row)) dot = "red";
  else if (row.chat_turn === "subscriber") dot = "wn";
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
