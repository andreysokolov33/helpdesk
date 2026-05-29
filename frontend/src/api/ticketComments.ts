export type TicketComment = {
  id: number;
  side: string;
  text: string;
  author_name: string;
  is_me?: boolean;
  created_at_iso?: string | null;
  is_edited?: boolean;
  updated_at_iso?: string | null;
};

export function isOwnTicketComment(c: TicketComment): boolean {
  return c.is_me === true || c.side === "me";
}

export type FetchTicketCommentsOpts = {
  sinceId?: number;
  beforeId?: number;
  afterId?: number;
  limit?: number;
};

export type TicketCommentsResult = {
  comments: TicketComment[];
  has_older?: boolean;
  has_newer?: boolean;
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

function buildCommentsQuery(opts?: FetchTicketCommentsOpts): string {
  const p = new URLSearchParams();
  if (opts?.sinceId && opts.sinceId > 0) {
    p.set("since_id", String(opts.sinceId));
  } else {
    if (opts?.beforeId && opts.beforeId > 0) p.set("before_id", String(opts.beforeId));
    if (opts?.afterId && opts.afterId > 0) p.set("after_id", String(opts.afterId));
    p.set("limit", String(opts?.limit ?? 40));
  }
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchTicketComments(
  ticketId: number,
  opts?: FetchTicketCommentsOpts,
): Promise<TicketCommentsResult> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/comments${buildCommentsQuery(opts)}`);
}

export async function sendTicketComment(ticketId: number, text: string): Promise<TicketComment> {
  const fd = new FormData();
  fd.set("text", text);
  const data = await apiJson<{ comment: TicketComment }>(
    `/api/v1/helpdesk/tracker/${ticketId}/comments`,
    { method: "POST", body: fd },
  );
  return data.comment;
}

export async function updateTicketComment(
  ticketId: number,
  commentId: number,
  text: string,
): Promise<TicketComment> {
  return apiJson(`/api/v1/helpdesk/tracker/${ticketId}/comments/${commentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function deleteTicketComment(ticketId: number, commentId: number): Promise<void> {
  await apiJson(`/api/v1/helpdesk/tracker/${ticketId}/comments/${commentId}`, { method: "DELETE" });
}

export function mergeTicketComments(prev: TicketComment[], incoming: TicketComment[]): TicketComment[] {
  if (!incoming.length) return prev;
  const map = new Map(prev.map((c) => [c.id, c]));
  for (const c of incoming) map.set(c.id, c);
  return [...map.values()].sort((a, b) => a.id - b.id);
}

export function maxTicketCommentId(comments: TicketComment[]): number {
  return comments.reduce((max, c) => Math.max(max, c.id), 0);
}

export function minTicketCommentId(comments: TicketComment[]): number | null {
  if (!comments.length) return null;
  return comments.reduce((min, c) => Math.min(min, c.id), comments[0].id);
}

import type { TicketMessage } from "@/api/ticket";

export function commentToMessage(c: TicketComment): TicketMessage {
  return {
    id: c.id,
    side: isOwnTicketComment(c) ? "me" : c.side,
    text: c.text,
    author_name: c.author_name,
    created_at_iso: c.created_at_iso,
    is_edited: c.is_edited,
    updated_at_iso: c.updated_at_iso,
    has_read: true,
    attachments: [],
  };
}
