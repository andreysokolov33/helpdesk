import { ticketListAssigneePill, type AssigneePillRow } from "@/api/tracker";

type Props = {
  row: AssigneePillRow;
  shortAssigneeName?: boolean;
};

/** Один исполнитель (assigned_to) — для списка /tickets. */
export default function TicketAssigneePill({ row, shortAssigneeName }: Props) {
  const pill = ticketListAssigneePill(row, { shortAssigneeName });
  return (
    <span
      className={`ch-assignee-pill ch-assignee-pill--${pill.variant}`}
      title={pill.title ?? pill.label}
    >
      {pill.label}
    </span>
  );
}
