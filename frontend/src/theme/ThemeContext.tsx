import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { nextTheme, parseStoredTheme, type AppTheme } from "@/theme/themeMeta";

export type { AppTheme };

const ThemeContext = createContext<{
  theme: AppTheme;
  toggleTheme: () => void;
  setTheme: (t: AppTheme) => void;
} | null>(null);

const STORAGE_KEY = "helpdesk-theme";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<AppTheme>(() => {
    if (typeof localStorage === "undefined") return "light";
    return parseStoredTheme(localStorage.getItem(STORAGE_KEY));
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((t: AppTheme) => setThemeState(t), []);
  const toggleTheme = useCallback(() => setThemeState((prev) => nextTheme(prev)), []);

  const value = useMemo(() => ({ theme, toggleTheme, setTheme }), [theme, toggleTheme, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme outside ThemeProvider");
  return ctx;
}
