import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useId, useRef, useState } from "react";
import { brandLogoSrc } from "@/brandLogos";
import { logoutRequest } from "@/api/auth";
import { getBellUnreadCount, MOCK_NOTIFS, NAV_CHATS_TAB_UNREAD } from "@/data/mockCc";
import { useTheme } from "@/theme/ThemeContext";

type TabDef = {
  to: string;
  label: string;
  end?: boolean;
  highlight?: boolean;
  badge?: number;
};

const tabs: TabDef[] = [
  { to: "/", label: "Главная", end: true },
  { to: "/call", label: "Регистрация звонка", highlight: true },
  { to: "/chats", label: "Чат", badge: NAV_CHATS_TAB_UNREAD },
  { to: "/stats", label: "Статистика" },
  { to: "/kb", label: "База знаний" },
];

function IconExit() {
  return (
    <svg className="nav-svg-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}

/** Солнце — текущая светлая тема. */
function IconSunScene({ gradId }: { gradId: string }) {
  return (
    <svg className="nav-theme-svg" viewBox="0 0 24 24" aria-hidden>
      <defs>
        <linearGradient id={gradId} x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FCD34D" />
          <stop offset="100%" stopColor="#F59E0B" />
        </linearGradient>
      </defs>
      <circle cx="12" cy="12" r="5" fill={`url(#${gradId})`} />
      <g stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round">
        <line x1="12" y1="1" x2="12" y2="3.5" />
        <line x1="12" y1="20.5" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.99" y2="5.99" />
        <line x1="18.01" y1="18.01" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3.5" y2="12" />
        <line x1="20.5" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.99" y2="18.01" />
        <line x1="18.01" y1="5.99" x2="19.78" y2="4.22" />
      </g>
    </svg>
  );
}

/** Закат / вечер — текущая тёмная тема. */
function IconSunsetScene({ skyId, glowId }: { skyId: string; glowId: string }) {
  return (
    <svg className="nav-theme-svg" viewBox="0 0 24 24" aria-hidden>
      <defs>
        <linearGradient id={skyId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#312E81" />
          <stop offset="45%" stopColor="#7C3AED" />
          <stop offset="72%" stopColor="#EA580C" />
          <stop offset="100%" stopColor="#C2410C" />
        </linearGradient>
        <radialGradient id={glowId} cx="50%" cy="100%" r="70%">
          <stop offset="0%" stopColor="#FDE047" stopOpacity="0.95" />
          <stop offset="55%" stopColor="#FB923C" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#FB923C" stopOpacity="0" />
        </radialGradient>
      </defs>
      <path fill={`url(#${skyId})`} d="M2 22V11c2.5-3 6-5 10-5s7.5 2 10 5v11H2Z" />
      <ellipse cx="12" cy="19" rx="10" ry="5" fill={`url(#${glowId})`} />
      <path
        fill="#FBBF24"
        d="M12 15.5a4.5 4.5 0 0 1-4.42-3.6 4.5 4.5 0 0 1 8.84 0A4.5 4.5 0 0 1 12 15.5Z"
      />
      <path stroke="rgba(255,255,255,.25)" strokeWidth="1" d="M2 17h20" strokeLinecap="round" />
    </svg>
  );
}

export default function DashboardShell() {
  const [notifOpen, setNotifOpen] = useState(false);
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const bellRef = useRef<HTMLButtonElement>(null);
  const themeGradId = useId().replace(/:/g, "");
  const sunsetSkyId = `${themeGradId}-sky`;
  const sunsetGlowId = `${themeGradId}-glow`;
  const sunGradId = `${themeGradId}-sun`;

  const bellUnread = getBellUnreadCount();

  useEffect(() => {
    function close(e: MouseEvent) {
      if (!notifOpen) return;
      if (bellRef.current?.contains(e.target as Node)) return;
      setNotifOpen(false);
    }
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [notifOpen]);

  async function performLogout() {
    await logoutRequest().catch(() => {});
    window.location.href = "/login";
  }

  function requestLogout() {
    const ok = window.confirm(
      "Выйти из Helpdesk? Текущая сессия будет завершена, потребуется войти снова.",
    );
    if (ok) void performLogout();
  }

  return (
    <div className="cc-app">
      <nav className="nav">
        <div className="nav-brand">
          <img
            src={brandLogoSrc(theme)}
            alt="WifiТочка"
            className="nav-brand-logo"
            height={36}
            width={160}
          />
          <span className="nav-product">Helpdesk</span>
        </div>

        <div className="nav-actions">
          <button
            type="button"
            className="nav-icon-btn nav-bell-btn"
            id="bellB"
            ref={bellRef}
            aria-expanded={notifOpen}
            aria-label="Уведомления"
            title="Уведомления"
            onClick={() => setNotifOpen((v) => !v)}
          >
            <svg className="nav-svg-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" aria-hidden>
              <path d="M12 3a4.5 4.5 0 0 0-4.5 4.5v2.4L6 13h12l-1.5-3.1V7.5A4.5 4.5 0 0 0 12 3Z" strokeLinejoin="round" />
              <path d="M9.2 18a2.8 2.8 0 0 0 5.6 0" strokeLinecap="round" />
            </svg>
            {bellUnread > 0 ? (
              <span className="nav-counter" aria-live="polite">
                {bellUnread > 99 ? "99+" : bellUnread}
              </span>
            ) : null}
            <div className={`ndd ${notifOpen ? "open" : ""}`}>
              <div className="ndh">Уведомления</div>
              {MOCK_NOTIFS.map((n) => (
                <NavLink
                  key={n.id}
                  className="ndi"
                  to={`/chats?id=${n.id}`}
                  onClick={() => setNotifOpen(false)}
                >
                  <span className="ndi-dot">●</span> {n.name} — {n.topic}
                  <div className="ndt">{n.ago}</div>
                </NavLink>
              ))}
            </div>
          </button>

          <button
            type="button"
            className="nav-icon-btn nav-theme-btn"
            onClick={toggleTheme}
            title={theme === "light" ? "Включить тёмную тему" : "Включить светлую тему"}
            aria-label={theme === "light" ? "Включить тёмную тему" : "Включить светлую тему"}
          >
            <span className={`nav-theme-fade ${theme === "light" ? "is-on" : ""}`}>
              <IconSunScene gradId={sunGradId} />
            </span>
            <span className={`nav-theme-fade ${theme === "dark" ? "is-on" : ""}`}>
              <IconSunsetScene skyId={sunsetSkyId} glowId={sunsetGlowId} />
            </span>
          </button>

          <button
            type="button"
            className="nav-icon-btn nav-exit-btn"
            onClick={requestLogout}
            title="Выйти"
            aria-label="Выйти из системы"
          >
            <IconExit />
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
              <span className="tab-highlight">
                <span className="tab-highlight-accent">Регистрация</span>
                <span className="tab-highlight-rest"> звонка</span>
              </span>
            ) : (
              <>
                <span className="tab-label">{t.label}</span>
                {typeof t.badge === "number" && t.badge > 0 ? (
                  <span className="tab-badge">{t.badge > 99 ? "99+" : t.badge}</span>
                ) : null}
              </>
            )}
          </NavLink>
        ))}
      </div>
      <Outlet key={location.pathname} />
    </div>
  );
}
