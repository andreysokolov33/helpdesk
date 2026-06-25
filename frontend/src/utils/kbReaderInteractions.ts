/** Интерактивность HTML-контента статей БЗ (табы ситуаций и т.п.). */

function activateTabGroup(buttons: HTMLButtonElement[], panes: HTMLElement[], index: number): void {
  buttons.forEach((btn, i) => btn.classList.toggle("active", i === index));
  panes.forEach((pane, i) => pane.classList.toggle("active", i === index));
}

/** Переключение вкладок `.tabs-header` → `.tab-content-container` (как в прототипе). */
export function bindKbReaderTabs(root: HTMLElement): () => void {
  const disposers: Array<() => void> = [];

  root.querySelectorAll(".tabs-header").forEach((header) => {
    const container = header.nextElementSibling;
    if (!container?.classList.contains("tab-content-container")) return;

    const buttons = Array.from(header.querySelectorAll<HTMLButtonElement>(".tab-btn"));
    const panes = Array.from(container.querySelectorAll<HTMLElement>(".tab-content-pane"));
    if (!buttons.length || !panes.length) return;

    const count = Math.min(buttons.length, panes.length);
    const activeIdx = buttons.findIndex((b) => b.classList.contains("active"));
    activateTabGroup(buttons, panes, activeIdx >= 0 ? activeIdx : 0);

    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const btn = target?.closest<HTMLButtonElement>(".tab-btn");
      if (!btn || !header.contains(btn)) return;
      event.preventDefault();

      const index = buttons.indexOf(btn);
      if (index < 0 || index >= count) return;
      activateTabGroup(buttons, panes, index);
    };

    header.addEventListener("click", onClick);
    disposers.push(() => header.removeEventListener("click", onClick));
  });

  return () => {
    disposers.forEach((dispose) => dispose());
  };
}
