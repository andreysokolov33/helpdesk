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

/** Просмотр картинок статьи: клик → лайтбокс на всю страницу. */
export function bindKbReaderImageLightbox(root: HTMLElement): () => void {
  const images = Array.from(root.querySelectorAll<HTMLImageElement>("img[src]")).filter(
    (img) => Boolean(img.getAttribute("src")?.trim()),
  );
  if (!images.length) return () => {};

  images.forEach((img) => {
    img.classList.add("kb-reader__img");
    img.setAttribute("role", "button");
    img.tabIndex = 0;
    if (!img.getAttribute("title")) {
      img.setAttribute("title", "Нажмите, чтобы увеличить");
    }
  });

  let overlay: HTMLDivElement | null = null;
  let currentIndex = 0;

  const close = () => {
    if (!overlay) return;
    overlay.remove();
    overlay = null;
    document.body.style.removeProperty("overflow");
    window.removeEventListener("keydown", onKeyDown, true);
  };

  const showAt = (index: number) => {
    if (!overlay || !images.length) return;
    currentIndex = ((index % images.length) + images.length) % images.length;
    const src = images[currentIndex]?.currentSrc || images[currentIndex]?.src || "";
    const alt = images[currentIndex]?.alt?.trim() || "Просмотр";
    const imgEl = overlay.querySelector<HTMLImageElement>(".kb-imgv__img");
    const counter = overlay.querySelector<HTMLElement>(".kb-imgv__counter");
    if (imgEl) {
      imgEl.src = src;
      imgEl.alt = alt;
    }
    if (counter) {
      counter.hidden = images.length < 2;
      counter.textContent = `${currentIndex + 1} / ${images.length}`;
    }
  };

  const open = (index: number) => {
    close();
    currentIndex = index;

    overlay = document.createElement("div");
    overlay.className = "kb-imgv";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Просмотр изображения");

    overlay.innerHTML = `
      <button type="button" class="kb-imgv__close" aria-label="Закрыть">×</button>
      <button type="button" class="kb-imgv__nav kb-imgv__nav--prev" aria-label="Предыдущее">‹</button>
      <div class="kb-imgv__box">
        <img class="kb-imgv__img" alt="" />
        <div class="kb-imgv__counter" aria-live="polite"></div>
      </div>
      <button type="button" class="kb-imgv__nav kb-imgv__nav--next" aria-label="Следующее">›</button>
    `;

    const prevBtn = overlay.querySelector<HTMLButtonElement>(".kb-imgv__nav--prev");
    const nextBtn = overlay.querySelector<HTMLButtonElement>(".kb-imgv__nav--next");
    if (images.length < 2) {
      prevBtn?.remove();
      nextBtn?.remove();
    }

    overlay.addEventListener("click", (event) => {
      const target = event.target as HTMLElement | null;
      if (!target || !overlay) return;
      if (target.closest(".kb-imgv__close")) {
        close();
        return;
      }
      if (target.closest(".kb-imgv__nav--prev")) {
        showAt(currentIndex - 1);
        return;
      }
      if (target.closest(".kb-imgv__nav--next")) {
        showAt(currentIndex + 1);
        return;
      }
      if (target === overlay || target.classList.contains("kb-imgv__box")) {
        close();
      }
    });

    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown, true);
    showAt(currentIndex);
  };

  function onKeyDown(event: KeyboardEvent): void {
    if (!overlay) return;
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopImmediatePropagation();
      close();
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      showAt(currentIndex - 1);
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      showAt(currentIndex + 1);
    }
  }

  const onRootClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement | null;
    const img = target?.closest("img");
    if (!img || !root.contains(img) || !images.includes(img as HTMLImageElement)) return;
    event.preventDefault();
    open(images.indexOf(img as HTMLImageElement));
  };

  const onRootKeyDown = (event: KeyboardEvent) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const target = event.target as HTMLElement | null;
    const img = target?.closest("img");
    if (!img || !root.contains(img) || !images.includes(img as HTMLImageElement)) return;
    event.preventDefault();
    open(images.indexOf(img as HTMLImageElement));
  };

  root.addEventListener("click", onRootClick);
  root.addEventListener("keydown", onRootKeyDown);

  return () => {
    close();
    root.removeEventListener("click", onRootClick);
    root.removeEventListener("keydown", onRootKeyDown);
    images.forEach((img) => {
      img.classList.remove("kb-reader__img");
      img.removeAttribute("role");
      img.removeAttribute("tabindex");
      if (img.getAttribute("title") === "Нажмите, чтобы увеличить") {
        img.removeAttribute("title");
      }
    });
  };
}

/** Вся интерактивность контента статьи. */
export function bindKbReaderInteractions(root: HTMLElement): () => void {
  const disposeTabs = bindKbReaderTabs(root);
  const disposeDiag = bindKbReaderDiagWidgets(root);
  const disposeGlossary = bindKbReaderGlossary(root);
  const disposeLightbox = bindKbReaderImageLightbox(root);
  return () => {
    disposeTabs();
    disposeDiag();
    disposeGlossary();
    disposeLightbox();
  };
}
