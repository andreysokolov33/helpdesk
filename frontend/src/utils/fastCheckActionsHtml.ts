/** Очистка HTML инструкций быстрой проверки: без inline script/style из БД. */
export function sanitizeFastCheckActionsHtml(html: string): string {
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, "");
}

async function copyQuiet(text: string): Promise<void> {
  const value = text.trim();
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    /* тихое копирование — без alert */
  }
}

function stripGuillemets(text: string): string {
  return text.replace(/^[«"]+/, "").replace(/[»"]+$/, "").trim();
}

function attachCopyTarget(el: HTMLElement, text: string) {
  const value = text.trim();
  if (!value) return;
  el.addEventListener("click", (e) => {
    e.preventDefault();
    void copyQuiet(value);
  });
}

/** Клик по тексту скрипта копирует в буфер; legacy copy-trigger из БД упрощается. */
export function bindFastCheckCopyHandlers(root: HTMLElement) {
  root.querySelectorAll(".copy-feedback").forEach((el) => el.remove());

  root.querySelectorAll(".copy-trigger").forEach((trigger) => {
    const text = trigger.getAttribute("data-copy-text")?.trim();
    const preview = trigger.parentElement?.querySelector<HTMLElement>(".script-preview");
    if (!text || !preview) return;

    preview.removeAttribute("style");
    preview.classList.remove("script-preview");
    attachCopyTarget(preview, text);

    const label = document.createTextNode("Скажите абоненту: ");
    trigger.replaceWith(label);
  });

  root.querySelectorAll<HTMLElement>("[data-copy-text]").forEach((el) => {
    if (el.classList.contains("copy-trigger")) return;
    const text = el.getAttribute("data-copy-text") ?? el.textContent ?? "";
    attachCopyTarget(el, text);
  });

  root.querySelectorAll<HTMLElement>(".fc-copy-text").forEach((el) => {
    const text = el.getAttribute("data-copy-text") ?? el.textContent ?? "";
    attachCopyTarget(el, stripGuillemets(text));
  });
}
