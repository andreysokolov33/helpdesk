export const TICKETS_LIST_PER_PAGE_OPTIONS = [10, 20, 50, 100] as const;

export type TicketsListPerPage = (typeof TICKETS_LIST_PER_PAGE_OPTIONS)[number];

const STORAGE_KEY = "helpdesk.tickets.perPageByUser";
const LEGACY_STORAGE_KEY = "helpdesk.chats.perPageByUser";
const DEFAULT_PER_PAGE: TicketsListPerPage = 20;

function isValidPerPage(value: unknown): value is TicketsListPerPage {
  return TICKETS_LIST_PER_PAGE_OPTIONS.includes(value as TicketsListPerPage);
}

function readPerPageMap(): Record<string, unknown> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Record<string, unknown>;
    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY);
    if (legacy) return JSON.parse(legacy) as Record<string, unknown>;
  } catch {
    /* ignore */
  }
  return {};
}

export function loadTicketsPerPage(userId: number): TicketsListPerPage {
  const value = readPerPageMap()[String(userId)];
  return isValidPerPage(value) ? value : DEFAULT_PER_PAGE;
}

export function saveTicketsPerPage(userId: number, perPage: TicketsListPerPage): void {
  try {
    const map: Record<string, number> = {};
    for (const [key, value] of Object.entries(readPerPageMap())) {
      if (isValidPerPage(value)) map[key] = value;
    }
    map[String(userId)] = perPage;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* ignore quota / private mode */
  }
}

/** @deprecated используйте loadTicketsPerPage */
export const loadChatsPerPage = loadTicketsPerPage;
/** @deprecated используйте saveTicketsPerPage */
export const saveChatsPerPage = saveTicketsPerPage;
export const CHATS_LIST_PER_PAGE_OPTIONS = TICKETS_LIST_PER_PAGE_OPTIONS;
export type ChatsListPerPage = TicketsListPerPage;
