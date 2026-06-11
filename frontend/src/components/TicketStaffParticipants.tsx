import { useState } from "react";
import { staffParticipantPill, type TicketStaffParticipant } from "@/api/tracker";

type Props = {
  participants: TicketStaffParticipant[];
  layout?: "sidebar" | "list";
};

function executorMoreLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `Ещё ${count} исполнитель`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `Ещё ${count} исполнителя`;
  }
  return `Ещё ${count} исполнителей`;
}

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

function CoExecutorRows({ others }: { others: TicketStaffParticipant[] }) {
  return (
    <>
      {others.map((p) => (
        <div className="tk-exec-co-row" key={p.id}>
          <ParticipantPill p={p} className="tk-exec-co-pill " />
        </div>
      ))}
    </>
  );
}

function SecondaryExecutorsSpoiler({ others }: { others: TicketStaffParticipant[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={`tk-exec-co-spoiler${open ? " tk-exec-co-spoiler--open" : ""}`}
      aria-label="Дополнительные исполнители"
    >
      <div className="tk-exec-co-spoiler__body">
        <div className="tk-exec-co-rows">
          <CoExecutorRows others={others} />
        </div>
      </div>
      <button
        type="button"
        className="tk-exec-co-spoiler__toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Свернуть" : executorMoreLabel(others.length)}
      </button>
    </div>
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
      {others.length > 0 ? <SecondaryExecutorsSpoiler others={others} /> : null}
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
