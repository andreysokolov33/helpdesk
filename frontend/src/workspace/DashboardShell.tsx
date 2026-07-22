import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { brandLogoSrc } from "@/brandLogos";
import { /* themeComfortIcon, */ themeMoonIcon, themeSunIcon } from "@/themeIcons";
import { fetchAuthMe, logoutRequest, type AuthMe } from "@/api/auth";
import { fetchDailyQuizStatus, type DailyQuizStatus } from "@/api/dailyQuiz";
import { sendOperatorPresence } from "@/api/operatorsManage";
import { fetchUnreadTicketsCount } from "@/api/ticketsNav";
import { fetchChatUnread } from "@/api/chat";
import { fetchOperatorNewsBell, fetchOperatorNewsBellDigest, fetchOperatorNewsDetail, formatNewsRelativeTime, isOperatorNewsUrgent, markOperatorNewsRead, operatorNewsKindLabel, type OperatorNewsBellItem, type OperatorNewsDetail } from "@/api/news";
import { ticketsListPollDelayMs } from "@/utils/ticketsListPoll";
import { useTheme } from "@/theme/ThemeContext";
import LogoutConfirmModal from "@/components/LogoutConfirmModal";
import OperatorNewsModal from "@/components/OperatorNewsModal";
import DailyQuizModal from "@/workspace/DailyQuizModal";
import { themeToggleHint } from "@/theme/themeMeta";

type TabDef = {
  to: string;
  label: string;
  end?: boolean;
  highlight?: boolean;
  badge?: number;
};

function outletResetKey(pathname: string): string {
  if (/^\/tickets\/\d+(?:\/|$)/.test(pathname)) return "/tickets/:ticketId";
  return pathname;
}

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
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [logoutBusy, setLogoutBusy] = useState(false);
  const [authMe, setAuthMe] = useState<AuthMe | null>(null);
  const [ticketsUnread, setTicketsUnread] = useState(0);
  const [chatUnread, setChatUnread] = useState(0);
  const [bellUnread, setBellUnread] = useState(0);
  const [bellItems, setBellItems] = useState<OperatorNewsBellItem[]>([]);
  const [newsModalOpen, setNewsModalOpen] = useState(false);
  const [newsDetail, setNewsDetail] = useState<OperatorNewsDetail | null>(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [dailyQuizOpen, setDailyQuizOpen] = useState(false);
  const [dailyQuizStatus, setDailyQuizStatus] = useState<DailyQuizStatus | null>(null);
  const bellDigestRef = useRef<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const bellRef = useRef<HTMLButtonElement>(null);
  const userMenuRef = useRef<HTMLButtonElement>(null);
  const userHead = userMenuHead(authMe);
  const hasUrgentUnread = useMemo(
    () => bellItems.some(isOperatorNewsUrgent),
    [bellItems],
  );
  const bellAttention = hasUrgentUnread && !notifOpen;

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
    if (!authMe) return;
    if ((authMe.role ?? "").toLowerCase() !== "support" || authMe.level !== 1) return;

    let cancelled = false;
    fetchDailyQuizStatus()
      .then((status) => {
        if (!cancelled && status.show_modal) {
          setDailyQuizStatus(status);
          setDailyQuizOpen(true);
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [authMe]);

  useEffect(() => {
    let cancelled = false;
    let pollTimer: number | null = null;

    async function loadUnread() {
      try {
        const count = await fetchUnreadTicketsCount();
        if (!cancelled) setTicketsUnread(count);
      } catch {
        if (!cancelled) setTicketsUnread(0);
      }
    }

    const schedulePoll = () => {
      pollTimer = window.setTimeout(() => {
        void loadUnread().finally(() => {
          if (!cancelled) schedulePoll();
        });
      }, ticketsListPollDelayMs());
    };

    void loadUnread();
    schedulePoll();

    function onVisible() {
      if (document.visibilityState === "visible") void loadUnread();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", loadUnread);

    return () => {
      cancelled = true;
      if (pollTimer != null) window.clearTimeout(pollTimer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", loadUnread);
    };
  }, [location.pathname]);

  useEffect(() => {
    let cancelled = false;
    let pollTimer: number | null = null;

    async function loadBellFull() {
      try {
        const data = await fetchOperatorNewsBell();
        if (!cancelled) {
          setBellUnread(data.unread_count);
          setBellItems(data.items);
        }
      } catch {
        if (!cancelled) {
          setBellUnread(0);
          setBellItems([]);
        }
      }
    }

    async function pollBellDigest() {
      try {
        const digest = await fetchOperatorNewsBellDigest({
          digest: bellDigestRef.current ?? undefined,
        });
        if (cancelled) return;
        bellDigestRef.current = digest.digest;
        setBellUnread(digest.unread_count);
        if (digest.changed) await loadBellFull();
      } catch {
        if (!cancelled) await loadBellFull();
      }
    }

    const schedulePoll = () => {
      pollTimer = window.setTimeout(() => {
        void pollBellDigest().finally(() => {
          if (!cancelled) schedulePoll();
        });
      }, ticketsListPollDelayMs());
    };

    void loadBellFull();
    schedulePoll();

    function onVisible() {
      if (document.visibilityState === "visible") void pollBellDigest();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", pollBellDigest);

    return () => {
      cancelled = true;
      if (pollTimer != null) window.clearTimeout(pollTimer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", pollBellDigest);
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

  useEffect(() => {
    let cancelled = false;

    async function ping() {
      if (document.visibilityState !== "visible") return;
      await sendOperatorPresence();
    }

    void ping();
    const timer = window.setInterval(() => void ping(), 30_000);

    function onVisible() {
      if (document.visibilityState === "visible" && !cancelled) void ping();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
  }, []);

  async function openNewsItem(item: OperatorNewsBellItem) {
    setNotifOpen(false);
    setNewsModalOpen(true);
    setNewsDetail(null);
    setNewsError(null);
    setNewsLoading(true);
    try {
      const detail = await fetchOperatorNewsDetail(item.id);
      setNewsDetail(detail);
      if (!detail.is_read) {
        await markOperatorNewsRead(item.id);
        setBellItems((prev) => prev.filter((n) => n.id !== item.id));
        setBellUnread((c) => Math.max(0, c - 1));
        bellDigestRef.current = null;
      }
    } catch (e) {
      setNewsError(e instanceof Error ? e.message : "Не удалось загрузить новость");
    } finally {
      setNewsLoading(false);
    }
  }

  function closeNewsModal() {
    setNewsModalOpen(false);
    setNewsDetail(null);
    setNewsError(null);
    setNewsLoading(false);
  }

  async function performLogout() {
    setLogoutBusy(true);
    try {
      await logoutRequest().catch(() => {});
      window.location.href = "/login";
    } finally {
      setLogoutBusy(false);
    }
  }

  function requestLogout() {
    setLogoutOpen(true);
  }

  const completeDailyQuiz = useCallback(() => {
    setDailyQuizOpen(false);
    setDailyQuizStatus(null);
  }, []);

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
            className={`nav-icon-btn nav-bell-btn${bellAttention ? " nav-bell-btn--urgent" : ""}`}
            id="bellB"
            ref={bellRef}
            aria-expanded={notifOpen}
            aria-label={bellAttention ? "Срочные уведомления" : "Уведомления"}
            title={bellAttention ? "Есть срочные непрочитанные уведомления" : "Уведомления"}
            onClick={() => setNotifOpen((v) => !v)}
          >
            <span className="nav-bell-ico-wrap" aria-hidden>
              <svg className="nav-svg-ico nav-bell-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85">
                <path d="M12 3a4.5 4.5 0 0 0-4.5 4.5v2.4L6 13h12l-1.5-3.1V7.5A4.5 4.5 0 0 0 12 3Z" strokeLinejoin="round" />
                <path d="M9.2 18a2.8 2.8 0 0 0 5.6 0" strokeLinecap="round" />
              </svg>
            </span>
            {bellUnread > 0 ? (
              <span className={`nav-counter${bellAttention ? " nav-counter--urgent" : ""}`} aria-live="polite">
                {bellUnread > 99 ? "99+" : bellUnread}
              </span>
            ) : null}
            <div className={`ndd ${notifOpen ? "open" : ""}`}>
              <div className="ndh">Уведомления</div>
              {bellItems.length === 0 ? (
                <div className="ndi ndi--empty">Нет новых уведомлений</div>
              ) : (
                bellItems.map((n) => {
                  const kindLabel = operatorNewsKindLabel(n.kind);
                  const important =
                    n.importance === "important" || n.importance === "featured";
                  return (
                    <button
                      key={n.id}
                      type="button"
                      className={`ndi ndi--news${important ? " ndi--important" : ""}`}
                      onClick={() => void openNewsItem(n)}
                    >
                      {important ? <span className="ndi-dot">●</span> : null}
                      {n.title}
                      <div className="ndt">
                        {kindLabel ? `${kindLabel} · ` : ""}
                        {formatNewsRelativeTime(n.published_at)}
                      </div>
                    </button>
                  );
                })
              )}
              <NavLink
                to="/news"
                className="ndd-foot"
                onClick={() => setNotifOpen(false)}
              >
                Все новости →
              </NavLink>
            </div>
          </button>

          <button
            type="button"
            className="nav-icon-btn nav-theme-btn"
            onClick={toggleTheme}
            title={themeToggleHint(theme)}
            aria-label={themeToggleHint(theme)}
          >
            <span className={`nav-theme-fade ${theme === "comfort" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeSunIcon} width={24} height={24} alt="" />
            </span>
            {/* Спрятанная тема «чистое солнце» (light) — не удалять
            <span className={`nav-theme-fade ${theme === "light" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeSunIcon} width={24} height={24} alt="" />
            </span>
            <span className={`nav-theme-fade ${theme === "comfort" ? "is-on" : ""}`}>
              <img className="nav-theme-svg" src={themeComfortIcon} width={24} height={24} alt="" />
            </span>
            */}
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
                    <span
                      className="tab-badge tab-badge--alert"
                      aria-label={
                        t.to === "/tickets"
                          ? authMe?.is_support_admin
                            ? `Открытых тикетов: ${badge}`
                            : `Требуют ответа: ${badge}`
                          : `Непрочитанных: ${badge}`
                      }
                    >
                      {badge > 99 ? "99+" : badge}
                    </span>
                  ) : null;
                })()}
              </>
            )}
          </NavLink>
        ))}
      </div>
      <Outlet key={outletResetKey(location.pathname)} />

      <LogoutConfirmModal
        open={logoutOpen}
        userName={userHead.title}
        userLogin={userHead.login}
        busy={logoutBusy}
        onClose={() => {
          if (!logoutBusy) setLogoutOpen(false);
        }}
        onConfirm={() => void performLogout()}
      />

      <OperatorNewsModal
        open={newsModalOpen}
        detail={newsDetail}
        loading={newsLoading}
        error={newsError}
        onClose={closeNewsModal}
      />

      {dailyQuizOpen && dailyQuizStatus ? (
        <DailyQuizModal
          status={dailyQuizStatus}
          onComplete={completeDailyQuiz}
        />
      ) : null}
    </div>
  );
}
