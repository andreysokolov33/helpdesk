import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { loginRequest } from "@/api/auth";
import { LogoMark } from "@/components/LogoMark";
import { useTheme } from "@/theme/ThemeContext";
import styles from "./LoginPage.module.css";

export default function LoginPage() {
  const [params] = useSearchParams();
  const next = params.get("next") || "/";
  const { theme, toggleTheme } = useTheme();

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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

  function fillDemo() {
    setLogin("operator");
    setPassword("demo");
  }

  return (
    <div className={styles.wrap} data-theme={theme}>
      <div className={styles.grid} aria-hidden />
      <div className={styles.themeRow}>
        <button type="button" className={styles.themeBtn} onClick={toggleTheme} title="Тема">
          {theme === "light" ? "🌙" : "☀️"}
        </button>
      </div>
      <div className={styles.card}>
        <div className={styles.brand}>
          <span className={styles.brandText}>WIFI</span>
          <LogoMark className={styles.mark} />
          <span className={styles.brandText}>ТОЧКА</span>
        </div>
        <h1 className={styles.title}>Helpdesk</h1>
        <p className={styles.sub}>Вход для линии техподдержки. Рабочий стол, чаты и база знаний.</p>
        <form onSubmit={onSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="login">
              Логин
            </label>
            <input
              id="login"
              name="username"
              autoComplete="username"
              className={styles.input}
              placeholder="Логин или email"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
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
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className={styles.btn} disabled={loading}>
            {loading ? "Вход…" : "Войти"}
          </button>
          {error ? <div className={styles.err}>{error}</div> : null}
        </form>
        <div className={styles.hint}>
          <button type="button" className={styles.hintBtn} onClick={fillDemo}>
            <span className={styles.tag}>Демо</span>
            <span className={styles.hintMid}>
              Подставить тестовые поля
              <div className={styles.hintSub}>замените на свои учётные данные</div>
            </span>
            <span className={styles.hintArrow}>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
