import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MOCK_SUBSCRIBERS } from "@/data/mockCc";

export default function CallTab() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [desc, setDesc] = useState("");
  const [found, setFound] = useState<(typeof MOCK_SUBSCRIBERS)[0] | null>(null);

  function onQ(v: string) {
    setQ(v);
    const s = v.trim().toLowerCase();
    if (s.length < 2) {
      setFound(null);
      return;
    }
    const m = MOCK_SUBSCRIBERS.find(
      (x) => x.n.toLowerCase().includes(s) || String(x.id).includes(s) || x.a.toLowerCase().includes(s),
    );
    setFound(m ?? null);
  }

  function submit() {
    if (!desc.trim()) {
      window.alert("Опишите обращение клиента");
      return;
    }
    const id = 400 + Math.floor(Math.random() * 90);
    navigate(`/chats?id=${id}`);
  }

  return (
    <div className="tp on">
      <div className="pg" style={{ maxWidth: 600 }}>
        <div style={{ fontSize: 16, fontWeight: 800 }}>
          <span style={{ color: "var(--red)" }}>Регистрация</span> звонка
        </div>
        <div
          style={{
            fontSize: 11,
            color: "var(--i3)",
            background: "var(--bg)",
            padding: "8px 12px",
            borderRadius: "var(--rs)",
            border: "1px solid var(--ln)",
          }}
        >
          Входящие звонки 8-800. Категория обращения выбирается при завершении заявки.
        </div>
        <div className="mf">
          <div className="mfl">1. Абонент</div>
          <input className="mi2" style={{ width: "100%" }} value={q} onChange={(e) => onQ(e.target.value)} placeholder="ФИО, ID, адрес…" />
          <div className={`mfd${found ? " vis" : ""}`}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700 }}>{found?.n}</div>
              <div style={{ fontSize: 10, color: "var(--i2)" }}>
                {found ? `ID ${found.id} · ${found.a} · ${found.c} · ${found.t}` : null}
              </div>
            </div>
          </div>
        </div>
        <div className="mf">
          <div className="mfl">2. Что говорит клиент</div>
          <textarea
            className="mta2"
            style={{ width: "100%", height: 80 }}
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="С утра нет интернета…"
          />
        </div>
        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
          <button type="button" className="tb" onClick={() => navigate("/")}>
            Отмена
          </button>
          <button
            type="button"
            style={{
              height: 34,
              padding: "0 16px",
              borderRadius: 6,
              border: "none",
              background: "var(--red)",
              color: "#fff",
              fontSize: 12,
              fontWeight: 700,
              cursor: "pointer",
            }}
            onClick={submit}
          >
            Создать заявку
          </button>
        </div>
      </div>
    </div>
  );
}
