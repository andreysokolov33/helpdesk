import { Link, useParams } from "react-router-dom";

export default function TicketStub() {
  const { ticketId } = useParams();
  return (
    <div className="tp on">
      <div className="pg">
        <div className="card">
          <div className="ct">Тикет #{ticketId}</div>
          <div className="cs2">Заглушка · раздел в разработке</div>
          <Link to="/chats" style={{ fontSize: 13, fontWeight: 700, color: "var(--red)" }}>
            ← К заявкам
          </Link>
        </div>
      </div>
    </div>
  );
}
