/** Интерактивность HTML-контента статей БЗ (табы ситуаций и т.п.). */

function activateTabGroup(buttons: HTMLButtonElement[], panes: HTMLElement[], index: number): void {
  buttons.forEach((btn, i) => btn.classList.toggle("active", i === index));
  panes.forEach((pane, i) => pane.classList.toggle("active", i === index));
}

function renderDiagResult(box: HTMLElement, status: string, action: string): void {
  box.replaceChildren();
  box.classList.add("is-visible");

  const requestLine = document.createElement("div");
  const requestLabel = document.createElement("strong");
  requestLabel.textContent = "Обращение абонента:";
  requestLine.append(requestLabel, document.createTextNode(` ${status}`));

  const actionLine = document.createElement("div");
  actionLine.className = "diag-result-action";
  const actionLabel = document.createElement("strong");
  actionLabel.textContent = "Действие оператора:";
  actionLine.append(actionLabel, document.createTextNode(` ${action}`));

  box.append(requestLine, actionLine);
}

/** Виджет «Диагностика показала → Действие» (.diag-widget). */
export function bindKbReaderDiagWidgets(root: HTMLElement): () => void {
  const disposers: Array<() => void> = [];

  root.querySelectorAll(".diag-widget").forEach((widget) => {
    const grid = widget.querySelector(".diag-grid");
    const resultBox = widget.querySelector<HTMLElement>(".diag-result-box");
    if (!grid || !resultBox) return;

    const buttons = Array.from(grid.querySelectorAll<HTMLButtonElement>(".diag-btn"));

    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const btn = target?.closest<HTMLButtonElement>(".diag-btn");
      if (!btn || !grid.contains(btn)) return;
      event.preventDefault();

      const status = btn.dataset.diagStatus?.trim();
      const action = btn.dataset.diagAction?.trim();
      if (!status || !action) return;

      buttons.forEach((item) => item.classList.toggle("is-active", item === btn));
      renderDiagResult(resultBox, status, action);
    };

    grid.addEventListener("click", onClick);
    disposers.push(() => grid.removeEventListener("click", onClick));
  });

  return () => {
    disposers.forEach((dispose) => dispose());
  };
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

/** Глоссарий: поиск и раскрытие карточек терминов. */
export function bindKbReaderGlossary(root: HTMLElement): () => void {
  const disposers: Array<() => void> = [];

  const searchInput =
    root.querySelector<HTMLInputElement>("#glossarySearch") ??
    root.querySelector<HTMLInputElement>(".search-wrap .search-input");
  const grid =
    root.querySelector<HTMLElement>("#termGridContainer") ??
    root.querySelector<HTMLElement>(".term-grid");

  if (grid) {
    const toggleCard = (card: HTMLElement) => {
      const wasActive = card.classList.contains("active-term");
      grid.querySelectorAll<HTMLElement>(".term-card").forEach((item) => {
        item.classList.remove("active-term");
        const btn = item.querySelector<HTMLElement>(".term-action-btn");
        if (btn) btn.textContent = "Показать скрипт";
      });
      if (!wasActive) {
        card.classList.add("active-term");
        const btn = card.querySelector<HTMLElement>(".term-action-btn");
        if (btn) btn.textContent = "Скрыть скрипт";
      }
    };

    const onGridClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const card = target?.closest<HTMLElement>(".term-card");
      if (!card || !grid.contains(card)) return;
      event.preventDefault();
      toggleCard(card);
    };

    grid.addEventListener("click", onGridClick);
    disposers.push(() => grid.removeEventListener("click", onGridClick));
  }

  if (searchInput && grid) {
    const filterCards = () => {
      const query = searchInput.value.toLowerCase().trim();
      grid.querySelectorAll<HTMLElement>(".term-card").forEach((card) => {
        const name = card.querySelector(".term-name")?.textContent?.toLowerCase() ?? "";
        const def = card.querySelector(".term-def")?.textContent?.toLowerCase() ?? "";
        const visible = !query || name.includes(query) || def.includes(query);
        card.style.display = visible ? "flex" : "none";
      });
    };

    searchInput.addEventListener("input", filterCards);
    disposers.push(() => searchInput.removeEventListener("input", filterCards));
  }

  return () => {
    disposers.forEach((dispose) => dispose());
  };
}

/** Вся интерактивность контента статьи. */
export function bindKbReaderInteractions(root: HTMLElement): () => void {
  const disposeTabs = bindKbReaderTabs(root);
  const disposeDiag = bindKbReaderDiagWidgets(root);
  const disposeGlossary = bindKbReaderGlossary(root);
  return () => {
    disposeTabs();
    disposeDiag();
    disposeGlossary();
  };
}
