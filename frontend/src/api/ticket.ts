export type TicketAttachment = {
  id: number;
  file_path: string;
  original_filename: string;
  file_ext?: string | null;
  file_size_bytes?: number | null;
  is_image?: boolean;
};

export type TicketMessage = {
  id: number;
  side: "client" | "agent" | "partner" | "bot" | string;
  text: string;
  created_at_iso?: string | null;
  has_read: boolean;
  author_name?: string | null;
  legacy_file_url?: string | null;
  attachments: TicketAttachment[];
  is_initial?: boolean;
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
  category_id?: number | null;
  category_parent_id?: number | null;
  user_id?: number | null;
  caller_name?: string | null;
  subscriber_name?: string | null;
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
  updated_at_iso?: string | null;
  assigned_at_iso?: string | null;
  chat_mode: "mail" | "tracker" | string;
  can_reply: boolean;
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

export async function fetchTicketMessages(ticketId: number): Promise<{ messages: TicketMessage[]; chat_mode: string }> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/messages`);
}

export async function sendTicketMessage(
  ticketId: number,
  text: string,
  file?: File | null,
): Promise<TicketMessage> {
  const fd = new FormData();
  fd.set("text", text);
  if (file) fd.set("file", file);
  const data = await apiJson<{ message: TicketMessage }>(`/api/v1/helpdesk/tracker/${ticketId}/messages`, {
    method: "POST",
    body: fd,
  });
  return data.message;
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
