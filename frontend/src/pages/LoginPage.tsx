import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { loginRequest } from "@/api/auth";
import { brandLogoSrc } from "@/brandLogos";
import { useTheme } from "@/theme/ThemeContext";
import { themeComfortIcon, themeMoonIcon, themeSunIcon } from "@/themeIcons";
import { themeToggleHint } from "@/theme/themeMeta";
import styles from "./LoginPage.module.css";

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
          <span className={`${styles.themeFade} ${theme === "light" ? styles.themeFadeOn : ""}`}>
            <img className={styles.themeIcon} src={themeSunIcon} width={22} height={22} alt="" />
          </span>
          <span className={`${styles.themeFade} ${theme === "comfort" ? styles.themeFadeOn : ""}`}>
            <img className={styles.themeIcon} src={themeComfortIcon} width={22} height={22} alt="" />
          </span>
          <span className={`${styles.themeFade} ${theme === "dark" ? styles.themeFadeOn : ""}`}>
            <img className={styles.themeIcon} src={themeMoonIcon} width={22} height={22} alt="" />
          </span>
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
