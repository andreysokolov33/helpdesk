import { staffParticipantPill, type TicketStaffParticipant } from "@/api/tracker";

type Props = {
  participants: TicketStaffParticipant[];
  layout?: "sidebar" | "list";
};

function ParticipantPill({
  p,
  className = "",
}: {
  p: TicketStaffParticipant;
  className?: string;
}) {
  const pill = staffParticipantPill(p);
  const primaryCls =
    p.is_primary && (p.role === "support" || !p.role) ? " ch-assignee-pill--primary" : "";
  return (
    <span
      className={`${className}ch-assignee-pill ch-assignee-pill--${pill.variant}${primaryCls}`}
      title={pill.title ?? (p.is_primary ? "Основной исполнитель" : pill.label)}
    >
      {pill.label}
    </span>
  );
}

/** Сайдбар тикета: основной в строке с подписью, соисполнители — отдельными строками на всю ширину. */
export function TicketSidebarExecutors({ participants }: { participants: TicketStaffParticipant[] }) {
  if (!participants.length) {
    return (
      <div className="tk-exec-block">
        <div className="kv tk-exec-kv">
          <span className="kvk">Исполнитель</span>
          <span className="kvv">
            <span className="tk-exec-primary-pill ch-assignee-pill ch-assignee-pill--unassigned">
              Нет исполнителя
            </span>
          </span>
        </div>
      </div>
    );
  }

  const primary = participants.find((p) => p.is_primary) ?? participants[0];
  const others = participants.filter((p) => p.id !== primary.id);

  return (
    <div className="tk-exec-block">
      <div className="kv tk-exec-kv">
        <span className="kvk">Исполнитель</span>
        <span className="kvv">
          <ParticipantPill p={primary} className="tk-exec-primary-pill " />
        </span>
      </div>
      {others.length > 0 ? (
        <div className="tk-exec-co-rows" aria-label="Соисполнители">
          {others.map((p) => (
            <div className="tk-exec-co-row" key={p.id}>
              <ParticipantPill p={p} className="tk-exec-co-pill " />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Список тикетов: все исполнители столбиком слева. */
export default function TicketStaffParticipants({ participants, layout = "list" }: Props) {
  if (layout === "sidebar") {
    return <TicketSidebarExecutors participants={participants} />;
  }

  if (!participants.length) {
    return (
      <span className="ch-assignee-pill ch-assignee-pill--unassigned" title="Нет исполнителя">
        Нет исполнителя
      </span>
    );
  }

  return (
    <span className="ch-coexecutors">
      {participants.map((p) => (
        <ParticipantPill key={p.id} p={p} />
      ))}
    </span>
  );
}
