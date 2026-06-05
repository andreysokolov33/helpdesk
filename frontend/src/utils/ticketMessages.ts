import {
  normalizeReadByReceipts,
  normalizeReadReceipts,
  type TicketMessage,
  type TicketMessageReadBy,
} from "@/api/ticket";

export function mergeTicketMessages(prev: TicketMessage[], incoming: TicketMessage[]): TicketMessage[] {
  if (!incoming.length) return prev;
  const map = new Map(prev.map((m) => [m.id, m]));
  for (const m of incoming) map.set(m.id, m);
  return [...map.values()].sort((a, b) => a.id - b.id);
}

export function maxTicketMessageId(messages: TicketMessage[]): number {
  return messages.reduce((max, m) => Math.max(max, m.id), 0);
}

export function isOwnTicketMessage(side: string): boolean {
  return side === "me";
}

export function isStaffOutboundMessage(side: string): boolean {
  return side === "me" || side === "support" || side === "engineer";
}

/** Контекстное меню: все сообщения кроме bot. */
export function canMessageContextMenu(side: string, messageId: number): boolean {
  if (messageId <= 0 || side === "bot") return false;
  return true;
}

export function mergeReadReceipts(
  prev: Record<number, string>,
  incoming: Record<number, string> | undefined,
): Record<number, string> {
  if (!incoming || !Object.keys(incoming).length) return prev;
  const next = { ...prev };
  for (const [k, v] of Object.entries(incoming)) {
    const id = Number(k);
    if (Number.isFinite(id) && id > 0 && v) next[id] = v;
  }
  return next;
}

export function mergeReadByReceipts(
  prev: Record<number, TicketMessageReadBy[]>,
  incoming: Record<number, TicketMessageReadBy[]> | undefined,
): Record<number, TicketMessageReadBy[]> {
  if (!incoming || !Object.keys(incoming).length) return prev;
  const next = { ...prev };
  for (const [k, readers] of Object.entries(incoming)) {
    const id = Number(k);
    if (Number.isFinite(id) && id > 0 && readers?.length) next[id] = readers;
  }
  return next;
}

export function mergeIncomingReadState(
  prevReceipts: Record<number, string>,
  prevReadBy: Record<number, TicketMessageReadBy[]>,
  raw?: { read_receipts?: Record<string, string>; read_by_receipts?: Record<string, TicketMessageReadBy[]> },
): { receipts: Record<number, string>; readBy: Record<number, TicketMessageReadBy[]> } {
  return {
    receipts: mergeReadReceipts(prevReceipts, normalizeReadReceipts(raw?.read_receipts)),
    readBy: mergeReadByReceipts(prevReadBy, normalizeReadByReceipts(raw?.read_by_receipts)),
  };
}

export function applyReadReceiptsToMessages<
  T extends {
    id: number;
    side: string;
    recipient_read_at_iso?: string | null;
    read_by?: TicketMessageReadBy[];
  },
>(
  messages: T[],
  receipts: Record<number, string>,
  readBy?: Record<number, TicketMessageReadBy[]>,
): T[] {
  const hasReceipts = Object.keys(receipts).length > 0;
  const hasReadBy = readBy && Object.keys(readBy).length > 0;
  if (!hasReceipts && !hasReadBy) return messages;
  return messages.map((m) => {
    if (!isStaffOutboundMessage(m.side)) return m;
    const hasReceipt = Object.prototype.hasOwnProperty.call(receipts, m.id);
    const hasReadBy = Boolean(readBy && Object.prototype.hasOwnProperty.call(readBy, m.id));
    const iso = hasReceipt ? receipts[m.id] : m.recipient_read_at_iso;
    const readers = hasReadBy ? readBy![m.id] : m.read_by;
    if (!iso && !readers?.length) return m;
    return {
      ...m,
      recipient_read_at_iso: iso ?? null,
      read_by: readers ?? [],
    };
  });
}

export function ticketMsgRowClass(side: string): string {
  if (side === "bot") return "msg bot";
  if (isOwnTicketMessage(side)) return "msg me";
  return `msg cl tk-msg--${side}`;
}

export function ticketBblClass(side: string): string {
  if (side === "bot") return "bbl bot";
  if (isOwnTicketMessage(side)) return "bbl ag";
  return `bbl cl tk-bbl--${side}`;
}

export function ticketMavClass(side: string): string {
  if (isOwnTicketMessage(side)) return "mav ag";
  return `mav cl tk-mav--${side}`;
}

export function ticketAuthorLabel(msg: TicketMessage, subscriberName: string): string {
  if (msg.author_name?.trim()) return msg.author_name.trim();
  if (msg.side === "bot") return "Бот";
  if (msg.side === "client") return subscriberName || "Абонент";
  if (msg.side === "partner") return "Партнёр";
  if (msg.side === "support") return "КЦ";
  if (msg.side === "engineer") return "Инженер";
  return "—";
}

export function ticketAvatarLetter(msg: TicketMessage, subscriberName: string): string {
  if (msg.side === "client") return subscriberName.trim()[0]?.toUpperCase() || "А";
  if (msg.side === "bot") return "Б";
  if (msg.side === "engineer") return "И";
  if (msg.side === "support") return (msg.author_name?.trim()[0] || "К").toUpperCase();
  if (msg.side === "partner") return "П";
  if (isOwnTicketMessage(msg.side)) return "Я";
  return "•";
}
