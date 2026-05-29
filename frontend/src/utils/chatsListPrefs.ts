export const CHATS_LIST_PER_PAGE_OPTIONS = [10, 20, 50, 100] as const;

export type ChatsListPerPage = (typeof CHATS_LIST_PER_PAGE_OPTIONS)[number];

const STORAGE_KEY = "helpdesk.chats.perPageByUser";
const DEFAULT_PER_PAGE: ChatsListPerPage = 20;

function isValidPerPage(value: unknown): value is ChatsListPerPage {
  return CHATS_LIST_PER_PAGE_OPTIONS.includes(value as ChatsListPerPage);
}

export function loadChatsPerPage(userId: number): ChatsListPerPage {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PER_PAGE;
    const map = JSON.parse(raw) as Record<string, unknown>;
    const value = map[String(userId)];
    return isValidPerPage(value) ? value : DEFAULT_PER_PAGE;
  } catch {
    return DEFAULT_PER_PAGE;
  }
}

export function saveChatsPerPage(userId: number, perPage: ChatsListPerPage): void {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const map: Record<string, number> = raw ? (JSON.parse(raw) as Record<string, number>) : {};
    map[String(userId)] = perPage;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* ignore quota / private mode */
  }
}
