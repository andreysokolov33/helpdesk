import { ticketListAssigneePill, type AssigneePillRow } from "@/api/tracker";

type Props = {
  row: AssigneePillRow;
};

/** Один исполнитель (assigned_to) — для списка /tickets. */
export default function TicketAssigneePill({ row }: Props) {
  const pill = ticketListAssigneePill(row);
  return (
    <span
      className={`ch-assignee-pill ch-assignee-pill--${pill.variant}`}
      title={pill.title ?? pill.label}
    >
      {pill.label}
    </span>
  );
}
