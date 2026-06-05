export type TicketAttachment = {
  id: number;
  file_path: string;
  original_filename: string;
  file_ext?: string | null;
  file_size_bytes?: number | null;
  is_image?: boolean;
};

export type TicketMessageReplyPreview = {
  id: number;
  author_name?: string | null;
  text: string;
  is_deleted?: boolean;
};

export type TicketMessageReadBy = {
  label: string;
  read_at_iso: string;
};

export type TicketMessage = {
  id: number;
  side: "client" | "support" | "engineer" | "partner" | "bot" | "me" | string;
  text: string;
  created_at_iso?: string | null;
  has_read: boolean;
  recipient_read_at_iso?: string | null;
  read_by?: TicketMessageReadBy[];
  reply_to_id?: number | null;
  is_edited?: boolean;
  updated_at_iso?: string | null;
  reply_preview?: TicketMessageReplyPreview | null;
  author_name?: string | null;
  legacy_file_url?: string | null;
  attachments: TicketAttachment[];
  is_initial?: boolean;
};

export type TicketSubscriberTariffSummary = {
  connected: boolean;
  state: string;
  tariff_name?: string | null;
  status_label: string;
  type_label?: string | null;
  frozen_at_label?: string | null;
  unfreeze_at_label?: string | null;
  frozen_remaining_label?: string | null;
  remain_traffic_mb?: number | null;
  full_packet_mb?: number | null;
  jur_main_packet_mb?: number | null;
  jur_dop_packet_mb?: number | null;
  overrun_mb?: number | null;
  rate_up?: string | null;
  rate_down?: string | null;
  msk_reset?: string | null;
  local_reset?: string | null;
  valid_date_label?: string | null;
  remaining_label?: string | null;
};

export type TicketSubscriberAccountSummary = {
  balance: number;
  tariff: TicketSubscriberTariffSummary;
};

export type TicketDetail = {
  id: number;
  title: string;
  body?: string | null;
  status: string;
  status_label: string;
  is_open: boolean;
  priority?: string | null;
  priority_label?: string | null;
  support_line: number;
  support_line_label: string;
  source: string;
  source_label: string;
  category_label?: string | null;
  category_name?: string | null;
  category_parent_name?: string | null;
  category_id?: number | null;
  category_parent_id?: number | null;
  user_id?: number | null;
  caller_name?: string | null;
  subscriber_name?: string | null;
  subscriber_display_name?: string | null;
  subscriber_login?: string | null;
  subscriber_online?: boolean;
  subscriber_is_juridical: number;
  subscriber_profile_user_id?: number | null;
  assignee_name?: string | null;
  assignee_role?: string | null;
  assignee_is_viewer: boolean;
  station_name?: string | null;
  station_id?: number | null;
  date_of_create_iso?: string | null;
  date_of_close_iso?: string | null;
  can_reopen?: boolean;
  updated_at_iso?: string | null;
  assigned_at_iso?: string | null;
  chat_mode: "mail" | "tracker" | string;
  can_reply: boolean;
  subscriber_account?: TicketSubscriberAccountSummary | null;
};

async function apiJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchTicketDetail(ticketId: number): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}`);
}

export async function linkTicketSubscriber(ticketId: number, userId: number): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/subscriber`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function transferTicketToEngineers(
  ticketId: number,
  payload: { categoryId: number; comment?: string },
): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/transfer-to-engineers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      category_id: payload.categoryId,
      comment: payload.comment?.trim() || null,
    }),
  });
}

export async function takeTicketBackToKs(ticketId: number): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/take-back-to-ks`, {
    method: "POST",
  });
}

export async function closeTicket(
  ticketId: number,
  payload: { categoryId: number; comment?: string },
): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/close`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      category_id: payload.categoryId,
      comment: payload.comment?.trim() || null,
    }),
  });
}

export async function reopenTicket(ticketId: number): Promise<TicketDetail> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/reopen`, { method: "POST" });
}

export type FetchTicketMessagesOpts = {
  sinceId?: number;
  beforeId?: number;
  afterId?: number;
  aroundId?: number;
  limit?: number;
};

export type TicketMessagesResult = {
  messages: TicketMessage[];
  chat_mode: string;
  read_receipts?: Record<string, string>;
  read_by_receipts?: Record<string, TicketMessageReadBy[]>;
  has_older?: boolean;
  has_newer?: boolean;
};

export type TicketReadReceiptsResult = {
  chat_mode: string;
  read_receipts?: Record<string, string>;
  read_by_receipts?: Record<string, TicketMessageReadBy[]>;
};

export type UploadTicketAttachmentResult = {
  token: string;
  original_filename: string;
  file_ext: string;
  file_size_bytes: number;
  is_image: boolean;
};

function buildMessagesQuery(opts?: FetchTicketMessagesOpts): string {
  const p = new URLSearchParams();
  if (opts?.sinceId && opts.sinceId > 0) {
    p.set("since_id", String(opts.sinceId));
  } else {
    if (opts?.beforeId && opts.beforeId > 0) p.set("before_id", String(opts.beforeId));
    if (opts?.afterId && opts.afterId > 0) p.set("after_id", String(opts.afterId));
    if (opts?.aroundId && opts.aroundId > 0) p.set("around_id", String(opts.aroundId));
    p.set("limit", String(opts?.limit ?? 40));
  }
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchTicketMessages(
  ticketId: number,
  opts?: FetchTicketMessagesOpts,
): Promise<TicketMessagesResult> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages${buildMessagesQuery(opts)}`);
}

/** Поллинг галочек «прочитано» на исходящих сообщениях. */
export async function fetchTicketReadReceipts(ticketId: number): Promise<TicketReadReceiptsResult> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages/reads`);
}

export async function uploadTicketAttachment(ticketId: number, file: File): Promise<UploadTicketAttachmentResult> {
  const fd = new FormData();
  fd.set("file", file);
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/attachments/upload`, { method: "POST", body: fd });
}

export async function detachTicketAttachment(
  ticketId: number,
  messageId: number,
  attachmentId: number,
): Promise<void> {
  await apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages/${messageId}/attachments/${attachmentId}`, {
    method: "DELETE",
  });
}

export function normalizeReadReceipts(raw?: Record<string, string>): Record<number, string> {
  if (!raw) return {};
  const out: Record<number, string> = {};
  for (const [k, v] of Object.entries(raw)) {
    const id = Number(k);
    if (Number.isFinite(id) && id > 0 && v) out[id] = v;
  }
  return out;
}

export function normalizeReadByReceipts(
  raw?: Record<string, TicketMessageReadBy[]>,
): Record<number, TicketMessageReadBy[]> {
  if (!raw) return {};
  const out: Record<number, TicketMessageReadBy[]> = {};
  for (const [k, readers] of Object.entries(raw)) {
    const id = Number(k);
    if (!Number.isFinite(id) || id <= 0 || !readers?.length) continue;
    const valid = readers.filter((r) => r?.label && r?.read_at_iso);
    if (valid.length) out[id] = valid;
  }
  return out;
}

export async function sendTicketMessage(
  ticketId: number,
  text: string,
  uploadTokens?: string[],
  file?: File | null,
  replyToId?: number | null,
): Promise<TicketMessage[]> {
  const fd = new FormData();
  fd.set("text", text);
  if (uploadTokens?.length) fd.set("upload_tokens", JSON.stringify(uploadTokens));
  if (file) fd.set("file", file);
  if (replyToId && replyToId > 0) fd.set("reply_to_id", String(replyToId));
  const data = await apiJson<{ message?: TicketMessage; messages?: TicketMessage[] }>(
    `/api/v1/helpdesk/tracker/${ticketId}/messages`,
    {
    method: "POST",
    body: fd,
    },
  );
  return data.messages?.length ? data.messages : data.message ? [data.message] : [];
}

export async function updateTicketMessage(
  ticketId: number,
  messageId: number,
  text: string,
): Promise<TicketMessage> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages/${messageId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function deleteTicketMessage(ticketId: number, messageId: number): Promise<void> {
  await apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages/${messageId}`, { method: "DELETE" });
}

import { formatDateTimeLocal } from "@/utils/dateTime";

export { formatDateTimeLocal, parseApiDate } from "@/utils/dateTime";

/** Время сообщения / краткая дата (локальный TZ пользователя). */
export function formatMsgTime(iso: string | null | undefined): string {
  return formatDateTimeLocal(iso);
}

/** Дата создания тикета в сайдбаре (с годом). */
export function formatTicketCreated(iso: string | null | undefined): string {
  return formatDateTimeLocal(iso, { withYear: true });
}
