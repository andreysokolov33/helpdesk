import logoForLightBg from "../../app/static/images/Logo_dark.svg?url";
import logoForDarkBg from "../../app/static/images/Logo_light.svg?url";

export type AppTheme = "light" | "dark";

/** Светлая тема интерфейса — тёмный логотип на светлом фоне. Тёмная — светлый логотип. */
export function brandLogoSrc(theme: AppTheme): string {
  return theme === "light" ? logoForLightBg : logoForDarkBg;
}
