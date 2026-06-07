import { Link, useParams } from "react-router-dom";

export default function UserProfileStub() {
  const { userId } = useParams();

  return (
    <div className="tp on">
      <div className="pg">
        <div className="card">
          <div className="ct">Карточка абонента</div>
          <div className="cs2">Заглушка · user_id: {userId ?? "—"}</div>
          <p style={{ fontSize: 13, color: "var(--i2)", lineHeight: 1.6 }}>
            Раздел в разработке. Путь: <code>/users/{userId}</code>
          </p>
          <Link to="/tickets" style={{ fontSize: 13, fontWeight: 700, color: "var(--red)" }}>
            ← К тикетам
          </Link>
        </div>
      </div>
    </div>
  );
}
