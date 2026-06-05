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
      <span className="tk-delivery__tick" aria-hidden>
        ✓
      </span>
      {read ? (
        <span className="tk-delivery__tick tk-delivery__tick--second" aria-hidden>
          ✓
        </span>
      ) : null}
    </span>
  );
}
