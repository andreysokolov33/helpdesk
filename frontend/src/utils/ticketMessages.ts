import type { TicketMessage } from "@/api/ticket";

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

export function applyReadReceiptsToMessages<T extends { id: number; side: string; recipient_read_at_iso?: string | null }>(
  messages: T[],
  receipts: Record<number, string>,
): T[] {
  if (!Object.keys(receipts).length) return messages;
  return messages.map((m) => {
    if (!isStaffOutboundMessage(m.side)) return m;
    const iso = receipts[m.id] ?? m.recipient_read_at_iso;
    if (!iso) return m;
    return { ...m, recipient_read_at_iso: iso };
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
