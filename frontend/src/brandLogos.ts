import logoForLightBg from "../../app/static/images/Logo_dark.svg?url";
import logoForDarkBg from "../../app/static/images/Logo_light.svg?url";
import type { AppTheme } from "@/theme/themeMeta";

/** Светлая и комфортная тема — тёмный логотип; тёмная — светлый логотип. */
export function brandLogoSrc(theme: AppTheme): string {
  return theme === "dark" ? logoForDarkBg : logoForLightBg;
}
