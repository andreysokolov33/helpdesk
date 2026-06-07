const CHAT_API = "/api/v1/helpdesk/chats";

export type ChatListItem = {
  chat_id: number;
  fullname: string;
  station_name?: string | null;
  last_message_text?: string | null;
  last_message_date_iso?: string | null;
  is_jur?: boolean;
  is_online?: number;
  has_unread?: boolean;
  unread_count: number;
  top_subscriber_rank?: number | null;
};

export type ChatAttachment = {
  id: number;
  file_path: string;
  original_filename: string;
  file_ext?: string | null;
  file_size_bytes?: number | null;
  is_image?: boolean;
};

export type ChatMessage = {
  msg_id: number;
  date_iso?: string | null;
  text: string;
  file_path?: string | null;
  answer: boolean;
  whose_message: string;
  author_kind?: "support" | "engineer" | "partner" | "subscriber" | string | null;
  has_read: boolean;
  user_id: number;
  subscriber_read_at?: string | null;
  relay_msg_id?: string | null;
  relay_author?: string | null;
  relay_snippet?: string | null;
  attachments: ChatAttachment[];
};

export type ChatMessagesResult = {
  messages: ChatMessage[];
  has_older?: boolean;
};

export type ChatReadBy = {
  label: string;
  read_at_iso: string;
  person_type?: string | null;
};

export type ChatUnreadStats = {
  opened_chats: number;
  opened_trackers: number;
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

export async function fetchChats(limit = 20, offset = 0): Promise<ChatListItem[]> {
  return apiJson(`${CHAT_API}/all?limit=${limit}&offset=${offset}`);
}

export async function fetchChatUpdates(lastSync: number): Promise<ChatListItem[]> {
  return apiJson(`${CHAT_API}/updates?last_sync=${encodeURIComponent(lastSync)}`);
}

export async function searchChats(query: string, limit = 20): Promise<ChatListItem[]> {
  return apiJson(`${CHAT_API}/search?query=${encodeURIComponent(query)}&limit=${limit}`);
}

export async function findOrCreateChat(userId: number): Promise<ChatListItem> {
  return apiJson(`${CHAT_API}/find-or-create?user_id=${userId}`);
}

export async function fetchChatUnread(): Promise<ChatUnreadStats> {
  return apiJson(`${CHAT_API}/unread_chats`);
}

export async function fetchChatMessages(
  chatId: number,
  opts?: { limit?: number; offset?: number; beforeId?: number; afterId?: number },
): Promise<ChatMessagesResult> {
  const p = new URLSearchParams();
  p.set("limit", String(opts?.limit ?? 20));
  if (opts?.offset) p.set("offset", String(opts.offset));
  if (opts?.beforeId && opts.beforeId > 0) p.set("before_id", String(opts.beforeId));
  if (opts?.afterId && opts.afterId > 0) p.set("after_id", String(opts.afterId));
  return apiJson(`${CHAT_API}/${chatId}/messages?${p.toString()}`);
}

export async function fetchChatMessageUpdates(chatId: number, afterId: number): Promise<ChatMessage[]> {
  const data = await apiJson<{ messages: ChatMessage[] }>(
    `${CHAT_API}/${chatId}/messages/updates?after_id=${afterId}`,
  );
  return data.messages ?? [];
}

export async function fetchChatReadReceipts(
  chatId: number,
  msgIds: number[],
): Promise<Record<number, ChatReadBy[]>> {
  if (!msgIds.length) return {};
  const data = await apiJson<{ read_by_receipts: Record<string, ChatReadBy[]> }>(
    `${CHAT_API}/${chatId}/messages/reads?msg_ids=${msgIds.join(",")}`,
  );
  const out: Record<number, ChatReadBy[]> = {};
  for (const [k, v] of Object.entries(data.read_by_receipts ?? {})) {
    const id = Number(k);
    if (Number.isFinite(id) && v?.length) out[id] = v;
  }
  return out;
}

export async function sendChatMessage(
  chatId: number,
  text: string,
  file?: File | null,
  replyToId?: number | null,
): Promise<ChatMessage> {
  const fd = new FormData();
  fd.set("text", text);
  if (file) fd.set("file", file);
  if (replyToId && replyToId > 0) fd.set("reply_to_id", String(replyToId));
  return apiJson(`${CHAT_API}/${chatId}/messages`, { method: "POST", body: fd });
}

export async function markChatRead(chatId: number, messageIds: number[]): Promise<void> {
  if (!messageIds.length) return;
  await apiJson(`${CHAT_API}/${chatId}/messages/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_ids: messageIds, person_type: "skystream" }),
  });
}

export async function editChatMessage(chatId: number, msgId: number, text: string): Promise<void> {
  await apiJson(`${CHAT_API}/${chatId}/messages/${msgId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function deleteChatMessage(chatId: number, msgId: number): Promise<void> {
  await apiJson(`${CHAT_API}/${chatId}/messages/${msgId}`, { method: "DELETE" });
}

/** Слить новые сообщения в существующий список без дублей, отсортировав по id. */
export function mergeChatMessages(prev: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  if (!incoming.length) return prev;
  const map = new Map<number, ChatMessage>();
  for (const m of prev) map.set(m.msg_id, m);
  for (const m of incoming) map.set(m.msg_id, m);
  return Array.from(map.values()).sort((a, b) => a.msg_id - b.msg_id);
}
