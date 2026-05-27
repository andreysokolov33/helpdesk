import { formatDateTimeLocal } from "@/utils/dateTime";
import { isStaffOutboundMessage } from "@/utils/ticketMessages";

type Props = {
  side: string;
  recipientReadAtIso?: string | null;
  ticketSource: string;
};

export default function TicketDeliveryTicks({ side, recipientReadAtIso, ticketSource }: Props) {
  if (!isStaffOutboundMessage(side)) return null;

  const isLk = ticketSource === "lk";
  const read = Boolean(recipientReadAtIso?.trim());
  const readLabel = formatDateTimeLocal(recipientReadAtIso, { withYear: true, withSeconds: true });

  const title = read
    ? isLk
      ? `Прочитано абонентом: ${readLabel}`
      : `Прочитано инженером: ${readLabel}`
    : isLk
      ? "Абонент ещё не прочитал"
      : "Инженер ещё не прочитал";

  return (
    <span
      className={`tk-delivery${read ? " tk-delivery--read" : ""}`}
      title={title}
      aria-label={title}
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
