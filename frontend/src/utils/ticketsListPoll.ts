/** Интервал поллинга списка /tickets и счётчика в навигации (+ джиттер против синхронных запросов). */
export const TICKETS_LIST_POLL_MS = 12_000;
export const TICKETS_LIST_POLL_JITTER_MS = 6_000;

export function ticketsListPollDelayMs(): number {
  const jitter = Math.floor(Math.random() * TICKETS_LIST_POLL_JITTER_MS);
  return TICKETS_LIST_POLL_MS + jitter;
}
