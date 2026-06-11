import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { brandLogoSrc } from "@/brandLogos";
import { themeComfortIcon, themeMoonIcon, themeSunIcon } from "@/themeIcons";
import { fetchAuthMe, logoutRequest, type AuthMe } from "@/api/auth";
import { fetchUnreadTicketsCount } from "@/api/ticketsNav";
import { fetchChatUnread } from "@/api/chat";
import { getBellUnreadCount, MOCK_NOTIFS } from "@/data/mockCc";
import { useTheme } from "@/theme/ThemeContext";
import { themeToggleHint } from "@/theme/themeMeta";

type TabDef = {
  to: string;
  label: string;
  end?: boolean;
  highlight?: boolean;
  badge?: number;
};

function userMenuHead(me: AuthMe | null): { title: string; login: string | null } {
  const login = me?.login?.trim() || null;
  const fullName = me?.full_name?.trim() || null;
  if (fullName) return { title: fullName, login };
  if (login) return { title: login, login: null };
  return { title: "Оператор", login: null };
}

const tabs: TabDef[] = [
  { to: "/", label: "Главная", end: true },
  { to: "/call", label: "Регистрация звонка", highlight: true },
  { to: "/tickets", label: "Тикеты" },
  { to: "/chat", label: "Чат" },
  { to: "/stats", label: "Статистика" },
  { to: "/kb", label: "База знаний" },
];

function IconUser() {
  return (
    <svg className="nav-svg-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" aria-hidden>
      <circle cx="12" cy="8" r="4" />
      <path strokeLinecap="round" d="M5 20c0-3.3 3.1-6 7-6s7 2.7 7 6" />
    </svg>
  );
}

export default function DashboardShell() {
  const [notifOpen, setNotifOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authMe, setAuthMe] = useState<AuthMe | null>(null);
  const [ticketsUnread, setTicketsUnread] = useState(0);
  const [chatUnread, setChatUnread] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const bellRef = useRef<HTMLButtonElement>(null);
  const userMenuRef = useRef<HTMLButtonElement>(null);
  const bellUnread = getBellUnreadCount();
  const userHead = userMenuHead(authMe);

  useEffect(() => {
    function close(e: MouseEvent) {
      const target = e.target as Node;
      if (notifOpen && !bellRef.current?.contains(target)) setNotifOpen(false);
      if (userMenuOpen && !userMenuRef.current?.contains(target)) setUserMenuOpen(false);
    }
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [notifOpen, userMenuOpen]);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((me) => {
        if (!cancelled) setAuthMe(me);
      })
      .catch(() => {
        if (!cancelled) setAuthMe(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadUnread() {
      try {
        const count = await fetchUnreadTicketsCount();
        if (!cancelled) setTicketsUnread(count);
      } catch {
        if (!cancelled) setTicketsUnread(0);
      }
    }

    void loadUnread();
    const timer = window.setInterval(loadUnread, 30_000);

    function onVisible() {
      if (document.visibilityState === "visible") void loadUnread();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", loadUnread);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", loadUnread);
    };
  }, [location.pathname]);

  useEffect(() => {
    let cancelled = false;

    async function loadChatUnread() {
      try {
        const stats = await fetchChatUnread();
        if (!cancelled) setChatUnread(stats.opened_chats ?? 0);
      } catch {
        if (!cancelled) setChatUnread(0);
      }
    }

    void loadChatUnread();
    const timer = window.setInterval(loadChatUnread, 10_000);

    function onVisible() {
      if (document.visibilityState === "visible") void loadChatUnread();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", loadChatUnread);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", loadChatUnread);
    };
  }, [location.pathname]);

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
                  to={`/tickets/${n.id}`}
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
            title={themeToggleHint(theme)}
            aria-label={themeToggleHint(theme)}
          >
            <span className={`nav-theme-fade ${theme === "light" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeSunIcon} width={24} height={24} alt="" />
            </span>
            <span className={`nav-theme-fade ${theme === "comfort" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeComfortIcon} width={24} height={24} alt="" />
            </span>
            <span className={`nav-theme-fade ${theme === "dark" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeMoonIcon} width={24} height={24} alt="" />
            </span>
          </button>

          <button
            type="button"
            className="nav-icon-btn nav-user-btn"
            ref={userMenuRef}
            aria-expanded={userMenuOpen}
            aria-label="Меню пользователя"
            title={userHead.title}
            onClick={() => setUserMenuOpen((v) => !v)}
          >
            <IconUser />
            <div className={`ndd nav-user-dd ${userMenuOpen ? "open" : ""}`}>
              <div className="ndh nav-user-head">
                <div className="nav-user-name">{userHead.title}</div>
                {userHead.login ? <div className="nav-user-login">{userHead.login}</div> : null}
              </div>
              <button
                type="button"
                className="ndi nav-user-item"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/account");
                }}
              >
                Профиль
              </button>
              <button
                type="button"
                className="ndi nav-user-logout"
                onClick={() => {
                  setUserMenuOpen(false);
                  requestLogout();
                }}
              >
                Выход
              </button>
            </div>
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
              <span className="tab-highlight-accent">Регистрация звонка</span>
            ) : (
              <>
                <span className="tab-label">{t.label}</span>
                {(() => {
                  const badge =
                    t.to === "/tickets" ? ticketsUnread : t.to === "/chat" ? chatUnread : t.badge;
                  return typeof badge === "number" && badge > 0 ? (
                    <span className="tab-badge tab-badge--alert" aria-label={`Непрочитанных: ${badge}`}>
                      {badge > 99 ? "99+" : badge}
                    </span>
                  ) : null;
                })()}
              </>
            )}
          </NavLink>
        ))}
      </div>
      <Outlet key={location.pathname} />
    </div>
  );
}
