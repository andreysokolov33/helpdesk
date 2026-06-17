import type { TicketMessageReadBy } from "@/api/ticket";
import { formatDateTimeLocal } from "@/utils/dateTime";
import { isOwnTicketMessage } from "@/utils/ticketMessages";

type Props = {
  side: string;
  recipientReadAtIso?: string | null;
  readBy?: TicketMessageReadBy[];
};

function formatReadLine(label: string, readAtIso: string): string {
  const when = formatDateTimeLocal(readAtIso, { withYear: true, withSeconds: true });
  return when ? `${label}: ${when}` : label;
}

function buildReadTooltip(readBy: TicketMessageReadBy[], fallbackReadAt?: string | null): string {
  if (readBy.length) {
    return readBy.map((r) => formatReadLine(r.label, r.read_at_iso)).join("\n");
  }
  if (fallbackReadAt?.trim()) {
    return formatReadLine("Прочитано", fallbackReadAt);
  }
  return "";
}

export default function TicketDeliveryTicks({ side, recipientReadAtIso, readBy }: Props) {
  if (!isOwnTicketMessage(side)) return null;

  const readers = readBy ?? [];
  const read = readers.length > 0 || Boolean(recipientReadAtIso?.trim());
  const tooltip = read
    ? buildReadTooltip(readers, recipientReadAtIso)
    : "Ещё не прочитано";

  return (
    <span
      className={`tk-delivery${read ? " tk-delivery--read" : ""}`}
      title={tooltip}
      aria-label={tooltip}
    >
      <svg className="tk-delivery__icon" width="15" height="10" viewBox="0 0 15 10" aria-hidden>
        {read ? (
          <>
            <path
              className="tk-delivery__path tk-delivery__path--first"
              d="M1 5.5L3.8 8.3L6.2 5.9"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.45"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              className="tk-delivery__path"
              d="M5.2 5.5L8 8.3L14 1.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.45"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </>
        ) : (
          <path
            className="tk-delivery__path"
            d="M1 5.5L4.5 9L14 1"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.45"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
      </svg>
    </span>
  );
}
