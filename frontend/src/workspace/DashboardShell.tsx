import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { LogoMark } from "@/components/LogoMark";
import { logoutRequest } from "@/api/auth";
import { MOCK_NOTIFS } from "@/data/mockCc";
import { useTheme } from "@/theme/ThemeContext";

const tabs = [
  { to: "/", label: "Главная", end: true },
  { to: "/call", label: "Регистрация звонка", highlight: true },
  { to: "/chats", label: "Чат", badge: 5 },
  { to: "/stats", label: "Статистика" },
  { to: "/kb", label: "База знаний" },
];

export default function DashboardShell() {
  const [notifOpen, setNotifOpen] = useState(false);
  const location = useLocation();
  const { toggleTheme } = useTheme();
  const bellRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    function close(e: MouseEvent) {
      if (!notifOpen) return;
      if (bellRef.current?.contains(e.target as Node)) return;
      setNotifOpen(false);
    }
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [notifOpen]);

  async function logout() {
    await logoutRequest().catch(() => {});
    window.location.href = "/login";
  }

  return (
    <div className="cc-app">
      <nav className="nav">
        <div className="logo">
          <span className="logo-wifi">WIFI</span>
          <LogoMark className="logo-mark" />
          <span className="logo-tochka">ТОЧКА</span>
          <span style={{ marginLeft: 10, fontSize: 11, fontWeight: 700, color: "var(--i3)" }}>Helpdesk</span>
        </div>
        <div className="nr" style={{ position: "relative" }}>
          <button
            type="button"
            className="ib"
            id="bellB"
            ref={bellRef}
            aria-expanded={notifOpen}
            onClick={() => setNotifOpen((v) => !v)}
          >
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
              <title>Уведомления</title>
              <path d="M10 2a5 5 0 00-5 5v3l-1.5 2.5h13L15 10V7a5 5 0 00-5-5z" />
              <path d="M8 16.5a2 2 0 004 0" />
            </svg>
            <span className="dot" />
            <div className={`ndd ${notifOpen ? "open" : ""}`}>
              <div className="ndh">Уведомления</div>
              {MOCK_NOTIFS.map((n) => (
                <NavLink
                  key={n.id}
                  className="ndi"
                  to={`/chats?id=${n.id}`}
                  onClick={() => setNotifOpen(false)}
                >
                  <span style={{ color: "var(--red)" }}>●</span> {n.name} — {n.topic}
                  <div className="ndt">{n.ago}</div>
                </NavLink>
              ))}
            </div>
          </button>
          <button type="button" className="ib" title="Тема" onClick={toggleTheme}>
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M17.3 11.3A8 8 0 118.7 2.7a6 6 0 008.6 8.6z" />
            </svg>
          </button>
          <button type="button" className="tb" onClick={logout}>
            Выйти
          </button>
        </div>
      </nav>
      <div className="tabs" id="ccT">
        {tabs.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.end}
            className={({ isActive }) => `tab${isActive ? " on" : ""}`}
          >
            {t.highlight ? (
              <span>
                <span style={{ color: "var(--red)", fontWeight: 700 }}>Регистрация</span> звонка
              </span>
            ) : (
              <>
                {t.label}
                {typeof t.badge === "number" ? <span className="c">{t.badge}</span> : null}
              </>
            )}
          </NavLink>
        ))}
      </div>
      <Outlet key={location.pathname} />
    </div>
  );
}
