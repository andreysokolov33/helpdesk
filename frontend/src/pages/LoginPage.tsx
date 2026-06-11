import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { loginRequest } from "@/api/auth";
import { brandLogoSrc } from "@/brandLogos";
import { useTheme } from "@/theme/ThemeContext";
import { themeComfortIcon } from "@/themeIcons";
import { nextTheme, themeToggleHint, type AppTheme } from "@/theme/themeMeta";
import styles from "./LoginPage.module.css";

function IconMoon() {
  return (
    <svg className={styles.themeGlyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="currentColor"
        d="M21.64 13a1 1 0 0 0-1.05-.14 8.05 8.05 0 0 1-3.37.73 8.15 8.15 0 0 1-8.14-8.1 8.59 8.59 0 0 1 .25-2A1 1 0 0 0 8 2.36a10.14 10.14 0 1 0 14 11.28 1 1 0 0 0-.36-1.64Z"
      />
    </svg>
  );
}

function IconSun() {
  return (
    <svg className={styles.themeGlyph} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
      <path
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"
      />
    </svg>
  );
}

function ThemeCycleIcon({ theme }: { theme: AppTheme }) {
  const next = nextTheme(theme);
  if (next === "dark") return <IconMoon />;
  if (next === "comfort") {
    return <img className={styles.themeGlyph} src={themeComfortIcon} width={22} height={22} alt="" />;
  }
  return <IconSun />;
}

function IconLock() {
  return (
    <svg className={styles.secureIcon} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="currentColor"
        d="M12 17a2 2 0 0 0 2-2v-2a2 2 0 1 0-4 0v2a2 2 0 0 0 2 2m6-7V9a6 6 0 1 0-12 0v1H4v14h16V10zm-2 0H8V9a4 4 0 1 1 8 0z"
      />
    </svg>
  );
}

export default function LoginPage() {
  const [params] = useSearchParams();
  const next = params.get("next") || "/";
  const { theme, toggleTheme } = useTheme();

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const logoSrc = brandLogoSrc(theme);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    const u = login.trim();
    if (u.length < 2) {
      setError("Введите логин (не короче 2 символов)");
      return;
    }
    if (password.length < 3) {
      setError("Пароль не короче 3 символов");
      return;
    }
    setLoading(true);
    try {
      const res = await loginRequest(u, password);
      const data = (await res.json().catch(() => ({}))) as {
        detail?: string | { msg?: string }[];
      };
      if (res.ok) {
        window.location.href = next.startsWith("/") ? next : "/";
        return;
      }
      let msg = "Ошибка входа";
      if (typeof data.detail === "string") msg = data.detail;
      else if (Array.isArray(data.detail))
        msg = data.detail.map((x) => (typeof x === "object" && x?.msg ? x.msg : String(x))).join("; ");
      setError(msg);
    } catch {
      setError("Сеть недоступна. Повторите попытку.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.wrap} data-theme={theme}>
      <div className={styles.aurora} aria-hidden />
      <div className={styles.mesh} aria-hidden />

      <header className={styles.topBar}>
        <button
          type="button"
          className={styles.themeBtn}
          onClick={toggleTheme}
          title={themeToggleHint(theme)}
          aria-label={themeToggleHint(theme)}
        >
          <ThemeCycleIcon theme={theme} />
        </button>
      </header>

      <main className={styles.main}>
        <section className={styles.card} aria-labelledby="login-heading">
          <div className={styles.logoBlock}>
            <img src={logoSrc} alt="WifiТочка" className={styles.brandLogo} width={200} height={48} />
          </div>
          <p className={styles.kicker}>Портал техподдержки</p>
          <h1 id="login-heading" className={styles.title}>
            Helpdesk
          </h1>
          <p className={styles.sub}>
            Рабочий стол линии поддержки: обращения, чаты и база знаний. Войдите под корпоративной учётной записью.
          </p>

          <form className={styles.form} onSubmit={onSubmit} noValidate>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="login">
                Логин
              </label>
              <input
                id="login"
                name="username"
                autoComplete="username"
                className={styles.input}
                placeholder="Учётная запись"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="password">
                Пароль
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                className={styles.input}
                placeholder="Введите пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>

            {error ? (
              <div className={styles.err} role="alert">
                {error}
              </div>
            ) : null}

            <button type="submit" className={styles.btn} disabled={loading}>
              <span className={styles.btnLabel}>{loading ? "Вход…" : "Войти"}</span>
              {loading ? <span className={styles.spinner} aria-hidden /> : null}
            </button>
          </form>

          <p className={styles.secure}>
            <IconLock />
            <span>Защищённое соединение, корпоративная авторизация</span>
          </p>
        </section>
      </main>
    </div>
  );
}
