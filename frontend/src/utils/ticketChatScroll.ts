export const CHAT_PAGE_SIZE = 20;
export const CHAT_SCROLL_EDGE_PX = 100;

export function isChatAtBottom(el: HTMLElement, threshold = CHAT_SCROLL_EDGE_PX): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
}

export function isChatNearTop(el: HTMLElement, threshold = CHAT_SCROLL_EDGE_PX): boolean {
  return el.scrollTop < threshold;
}

export function isChatNearBottom(el: HTMLElement, threshold = CHAT_SCROLL_EDGE_PX): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
}

export function preserveScrollOnPrepend(el: HTMLElement, prevHeight: number, prevTop: number): void {
  el.scrollTop = prevTop + (el.scrollHeight - prevHeight);
}

export function scrollChatToBottom(el: HTMLElement): void {
  el.scrollTop = el.scrollHeight;
}

export function minLoadedMessageId(messages: { id: number }[]): number | null {
  const ids = messages.map((m) => m.id).filter((id) => id > 0);
  return ids.length ? Math.min(...ids) : null;
}

export function maxLoadedMessageId(messages: { id: number }[]): number {
  return messages.reduce((max, m) => Math.max(max, m.id), 0);
}
