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
  el.scrollTop = Math.max(0, el.scrollHeight - el.clientHeight);
}

/**
 * Удерживает скролл внизу при первой загрузке: картинки и шрифты меняют scrollHeight
 * уже после первого scrollTop.
 */
export function watchChatScrollToBottom(el: HTMLElement, maxMs = 2500): () => void {
  let active = true;
  const snap = () => {
    if (!active) return;
    const last = el.querySelector("[data-msg-id]:last-of-type") as HTMLElement | null;
    if (last) {
      last.scrollIntoView({ block: "end", inline: "nearest" });
    }
    scrollChatToBottom(el);
  };

  snap();
  requestAnimationFrame(() => requestAnimationFrame(snap));

  const ro = new ResizeObserver(() => snap());
  const feed = el.querySelector(".tk-chat-feed, .cs-feed");
  if (feed) ro.observe(feed);
  ro.observe(el);

  const timers = [0, 50, 150, 400, 800, 1500].map((ms) => window.setTimeout(snap, ms));
  const stopTimer = window.setTimeout(() => {
    active = false;
    ro.disconnect();
  }, maxMs);

  return () => {
    active = false;
    ro.disconnect();
    timers.forEach((id) => window.clearTimeout(id));
    window.clearTimeout(stopTimer);
  };
}

export function minLoadedMessageId(messages: { id: number }[]): number | null {
  const ids = messages.map((m) => m.id).filter((id) => id > 0);
  return ids.length ? Math.min(...ids) : null;
}

export function maxLoadedMessageId(messages: { id: number }[]): number {
  return messages.reduce((max, m) => Math.max(max, m.id), 0);
}
