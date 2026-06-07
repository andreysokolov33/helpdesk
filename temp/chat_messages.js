/**
 * CHAT MESSAGES: Окно переписки, галерея и поллинг сообщений
 */
(function (App) {
    if (!App) return console.error("ChatApp Core not found!");
    const { UI, STATE, Utils } = App;
    const MAX_FILES_PER_MESSAGE = 10;

    // ==========================================
    // 1. КЛАСС ГАЛЕРЕИ (ПРОСМОТР КАРТИНОК)
    // ==========================================
    class ChatGallery {
        constructor() {
            this.modal = document.getElementById('gallery-modal');
            this.img = document.getElementById('gallery-img');
            this.counter = document.getElementById('gallery-counter');
            this.images = [];
            this.currentIndex = 0;
            this.init();
        }

        init() {
            // Кнопки управления
            this.modal.querySelector('.gallery-close').onclick = () => this.close();
            this.modal.querySelector('.gallery-prev').onclick = () => this.changeImg(-1);
            this.modal.querySelector('.gallery-next').onclick = () => this.changeImg(1);

            // Закрытие по клику на любое пространство вне картинки
            this.modal.onclick = (e) => {
                if (e.target === this.modal) this.close();
            };

            // Управление клавиатурой
            document.addEventListener('keydown', (e) => {
                if (!this.modal.classList.contains('show')) return;
                if (e.key === "Escape") this.close();
                if (e.key === "ArrowLeft") this.changeImg(-1);
                if (e.key === "ArrowRight") this.changeImg(1);
            });
            window.addEventListener('resize', () => {
                this.updateHeaderButtonsVisibility();
            });
        }

        open(clickedSrc) {
            const root = (UI.messagesList && UI.messagesList.querySelectorAll) ? UI.messagesList : document;
            const allImgElements = Array.from(root.querySelectorAll('.message-image-thumb, .message-image'));
            const validImgElements = allImgElements.filter(img => img.style.display !== 'none');
            if (validImgElements.length === 0) return;
            this.images = validImgElements.map(el => el.src);
            this.images.reverse();
            this.currentIndex = this.images.indexOf(clickedSrc);
            if (this.currentIndex === -1) this.currentIndex = 0;
            this.showImage();
            this.modal.classList.add('show');
        }

        prependToGallery(newUrls) {
            if (!newUrls || newUrls.length === 0) return;
            if (!this.modal.classList.contains('show')) return;
            this.images = newUrls.concat(this.images);
            this.currentIndex += newUrls.length;
            this.showImage();
        }

        openWithUrls(urls, index) {
            if (!urls || urls.length === 0) return;
            this.images = urls;
            this.currentIndex = Math.min(index || 0, urls.length - 1);
            this.showImage();
            this.modal.classList.add('show');
        }

        close() { this.modal.classList.remove('show'); }

        changeImg(dir) {
            if (this.images.length <= 1) return;
            this.currentIndex = (this.currentIndex + dir + this.images.length) % this.images.length;
            this.showImage();
        }

        showImage() {
            this.img.src = this.images[this.currentIndex];
            this.counter.textContent = `${this.currentIndex + 1} из ${this.images.length}`;

            // Скрываем стрелки, если картинка всего одна (CSS класс single-image)
            if (this.images.length <= 1) {
                this.modal.classList.add('single-image');
            } else {
                this.modal.classList.remove('single-image');
            }
        }
    }

    // ==========================================
    // 2. ОБЪЕКТ УПРАВЛЕНИЯ СООБЩЕНИЯМИ
    // ==========================================
    App.Messages = {
        gallery: null,

        init() {
            this.gallery = new ChatGallery();
            this.bindEvents();
        },

        getEditorHtml() {
            return (UI.input && (UI.input.innerHTML || "").trim()) || "";
        },
        setEditorHtml(html) {
            if (!UI.input) return;
            UI.input.innerHTML = (html == null || html === "") ? "" : String(html);
        },
        execFormat(cmd) {
            if (!UI.input) return;
            UI.input.focus();
            if (document.execCommand && document.queryCommandSupported(cmd)) document.execCommand(cmd, false, null);
        },
        insertLink() {
            if (!UI.input) return;
            UI.input.focus();
            const sel = window.getSelection();
            const range = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
            const linkModal = document.getElementById("chat-link-modal-backdrop");
            const urlInput = document.getElementById("chat-link-url");
            const textInput = document.getElementById("chat-link-text");
            if (!linkModal || !urlInput || !textInput) return;
            urlInput.value = "https://";
            textInput.value = (range && !range.collapsed) ? sel.toString() : "";
            linkModal.classList.remove("hidden");
            urlInput.focus();
            const submit = () => {
                let url = (urlInput.value || "").trim();
                let text = (textInput.value || "").trim() || "ссылка";
                linkModal.classList.add("hidden");
                if (!url) return;
                if (!url.startsWith("http://") && !url.startsWith("https://") && !url.startsWith("/")) {
                    DarkToast?.error?.("Допустимы только ссылки, начинающиеся с http://, https:// или /") || alert("Допустимы только ссылки...");
                    return;
                }
                const safeUrl = url.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
                const safeText = String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                const html = "<a href=\"" + safeUrl + "\" target=\"_blank\" rel=\"noopener\">" + safeText + "</a>";
                if (document.execCommand && document.queryCommandSupported("insertHTML")) {
                    if (range && !range.collapsed) {
                        range.deleteContents();
                        const frag = document.createRange().createContextualFragment(html);
                        range.insertNode(frag);
                    } else document.execCommand("insertHTML", false, html);
                } else {
                    const a = document.createElement("a");
                    a.href = url;
                    a.setAttribute("target", "_blank");
                    a.setAttribute("rel", "noopener");
                    a.textContent = text;
                    if (range) { range.deleteContents(); range.insertNode(a); } else UI.input.appendChild(a);
                }
            };
            const cancel = () => linkModal.classList.add("hidden");
            document.getElementById("chat-link-modal-submit").onclick = submit;
            document.getElementById("chat-link-modal-cancel").onclick = cancel;
            linkModal.onclick = (e) => { if (e.target === linkModal) cancel(); };
            const once = (fn) => { const g = () => { fn(); urlInput.removeEventListener("keydown", g); textInput.removeEventListener("keydown", g); }; return g; };
            urlInput.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); submit(); } if (e.key === "Escape") cancel(); };
            textInput.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); submit(); } if (e.key === "Escape") cancel(); };
        },
        applyTextColor(className) {
            if (!UI.input) return;
            UI.input.focus();
            const sel = window.getSelection();
            const range = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
            if (!range || range.collapsed) return;
            const span = document.createElement("span");
            span.className = className;
            try { range.surroundContents(span); } catch (e) {
                const content = range.toString();
                range.deleteContents();
                span.textContent = content;
                range.insertNode(span);
            }
        },
        formatBlock(blockTag) {
            if (!UI.input) return;
            const sel = window.getSelection();
            const savedRange = this._headingSavedRange;
            if (savedRange) {
                UI.input.focus();
                sel.removeAllRanges();
                try { sel.addRange(savedRange); } catch (e) { /* ignore */ }
                this._headingSavedRange = null;
            } else {
                UI.input.focus();
            }
            if (document.execCommand && document.queryCommandSupported("formatBlock")) {
                document.execCommand("formatBlock", false, blockTag);
            } else {
                this._formatBlockFallback(blockTag);
            }
        },
        _formatBlockFallback(blockTag) {
            const sel = window.getSelection();
            if (!sel.rangeCount || !UI.input) return;
            const range = sel.getRangeAt(0);
            if (!UI.input.contains(range.commonAncestorContainer)) return;
            const tag = blockTag.toUpperCase();
            if (["H1", "H2", "H3", "H4", "H5", "H6", "P"].indexOf(tag) === -1) return;
            const el = document.createElement(blockTag);
            try {
                range.surroundContents(el);
            } catch (e) {
                range.deleteContents();
                el.textContent = "\u00a0";
                range.insertNode(el);
            }
        },
        bindChatToolbar() {
            document.querySelectorAll(".chat-toolbar-btn[data-cmd]").forEach(btn => {
                btn.addEventListener("click", () => this.execFormat(btn.dataset.cmd));
            });
            const linkBtn = document.getElementById("chat-link-btn");
            if (linkBtn) linkBtn.addEventListener("click", () => this.insertLink());
            const headingBtn = document.getElementById("chat-heading-btn");
            const headingDropdown = document.getElementById("chat-heading-dropdown");
            if (headingBtn && headingDropdown) {
                headingBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    const wasHidden = headingDropdown.classList.contains("hidden");
                    headingDropdown.classList.toggle("hidden");
                    if (wasHidden) {
                        const sel = window.getSelection();
                        if (sel.rangeCount && UI.input && UI.input.contains(sel.anchorNode)) {
                            try { this._headingSavedRange = sel.getRangeAt(0).cloneRange(); } catch (err) { this._headingSavedRange = null; }
                        } else this._headingSavedRange = null;
                        if (!headingDropdown.classList.contains("hidden")) {
                            headingDropdown.classList.remove("open-up");
                            requestAnimationFrame(() => {
                                const rect = headingDropdown.getBoundingClientRect();
                                const reserve = 120;
                                if (rect.bottom > window.innerHeight - reserve) headingDropdown.classList.add("open-up");
                            });
                        }
                    } else {
                        headingDropdown.classList.remove("open-up");
                    }
                });
                headingDropdown.querySelectorAll(".chat-heading-opt").forEach(opt => {
                    opt.addEventListener("mousedown", (e) => e.preventDefault());
                    opt.addEventListener("click", () => {
                        this.formatBlock(opt.dataset.block);
                        headingDropdown.classList.add("hidden");
                        headingDropdown.classList.remove("open-up");
                    });
                });
                document.addEventListener("click", (e) => {
                    if (!headingDropdown.classList.contains("hidden") && !headingDropdown.contains(e.target) && e.target !== headingBtn) {
                        headingDropdown.classList.add("hidden");
                        headingDropdown.classList.remove("open-up");
                    }
                });
            }
            const colorBtn = document.getElementById("chat-color-btn");
            const colorDropdown = document.getElementById("chat-color-dropdown");
            if (colorBtn && colorDropdown) {
                colorBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    colorDropdown.classList.toggle("hidden");
                    if (!colorDropdown.classList.contains("hidden")) {
                        colorDropdown.classList.remove("open-up");
                        requestAnimationFrame(() => {
                            const rect = colorDropdown.getBoundingClientRect();
                            const reserve = 120;
                            if (rect.bottom > window.innerHeight - reserve) colorDropdown.classList.add("open-up");
                        });
                    }
                });
                colorDropdown.querySelectorAll(".chat-color-opt").forEach(opt => {
                    opt.addEventListener("click", () => {
                        this.applyTextColor(opt.getAttribute("data-class"));
                        colorDropdown.classList.add("hidden");
                        colorDropdown.classList.remove("open-up");
                    });
                });
            }
            document.addEventListener("click", (e) => {
                if (colorDropdown && !colorDropdown.classList.contains("hidden") && !colorDropdown.contains(e.target) && e.target !== colorBtn) {
                    colorDropdown.classList.add("hidden");
                    colorDropdown.classList.remove("open-up");
                }
            });
        },

        bindEvents() {
            // Отправка формы
            UI.form.onsubmit = (e) => { e.preventDefault(); this.handleSend(); };

            UI.cancelEditBtn.onclick = () => this.resetInput();
            if (UI.replyCloseBtn) UI.replyCloseBtn.onclick = () => this.clearReplyTo();

            // Автоподгрузка при скролле вверх
            this.setupLoadMoreObserver();

            // Контекстное меню (ПКМ)
            this.bindContextMenu();

            window.addEventListener('hashchange', () => this.applyMessageLinkHash());

            if (UI.messagesContainer) {
                UI.messagesContainer.addEventListener("scroll", () => {
                    requestAnimationFrame(() => this.updateScrollToBottomBtn());
                });
            }
            if (UI.scrollToBottomBtn) UI.scrollToBottomBtn.addEventListener("click", () => this.scrollToBottom());
            window.addEventListener("resize", () => {
                if (STATE.currentChatId && UI.messagesContainer) requestAnimationFrame(() => this.updateScrollToBottomBtn());
            });

            // Обработка выбора файлов (несколько, до 15 МБ каждый) — превью-сетка
            const MAX_FILE_MB = 15;
            const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;
            const ALLOWED_EXT = new Set(["pdf", "xlsx", "xls", "doc", "docx", "docm", "csv", "jpg", "jpeg", "png", "gif", "webp", "bmp"]);
            const isAllowedFile = (file) => {
                if (file.type && file.type.startsWith("image/")) return true;
                const ext = (file.name || "").split(".").pop()?.toLowerCase();
                return ext && ALLOWED_EXT.has(ext);
            };
            UI.fileInput.onchange = (e) => {
                const newFiles = Array.from(e.target.files || []);
                if (newFiles.length === 0) return;
                const disallowed = newFiles.filter(f => !isAllowedFile(f));
                if (disallowed.length > 0) {
                    DarkToast.error(`Допустимы только PDF, Excel (XLS, XLSX), Word (DOC, DOCX), CSV и изображения. Не загружены: ${disallowed.map(f => f.name).join(", ")}`);
                    e.target.value = "";
                    return;
                }
                const over = newFiles.filter(f => (f.size || 0) > MAX_FILE_BYTES);
                if (over.length > 0) {
                    DarkToast.error(`Файлы более ${MAX_FILE_MB} МБ не допускаются: ${over.map(f => f.name).join(", ")}`);
                    e.target.value = "";
                    return;
                }
                STATE.selectedFiles = [...(STATE.selectedFiles || []), ...newFiles];
                e.target.value = "";
                this.renderFilePreviewGrid();
            };
            if (UI.removeAllFilesBtn) UI.removeAllFilesBtn.onclick = () => this.clearFileSelection();

            UI.messagesList.onclick = (e) => this.handleListClick(e);
            UI.messagesList.addEventListener("keydown", (e) => {
                const replyBlock = e.target.closest(".message-reply-to");
                if (replyBlock && (e.key === "Enter" || e.key === " ")) {
                    e.preventDefault();
                    if (replyBlock.dataset.replyToMsgId) this.loadMessagesAround(Number(replyBlock.dataset.replyToMsgId));
                }
            });

            // Отправка по Ctrl+Enter
            UI.input.onkeydown = (e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    UI.form.requestSubmit();
                }
            };
            this.bindChatToolbar();
            const infoBtn = document.getElementById('open-info-btn');
            if (infoBtn) {
                infoBtn.onclick = () => App.Info.load();
            }
        },

        renderFilePreviewGrid() {
            const grid = UI.filePreviewGrid;
            if (!grid) return;
            grid.innerHTML = "";
            const getFileIconClass = (ext) => {
                const e = (ext || "").toLowerCase();
                if (["doc", "docx", "docm"].includes(e)) return "file-preview-tile-icon--docx";
                if (e === "pdf") return "file-preview-tile-icon--pdf";
                if (["xls", "xlsx"].includes(e)) return "file-preview-tile-icon--xlsx";
                if (e === "csv") return "file-preview-tile-icon--csv";
                return "file-preview-tile-icon--default";
            };
            const fmtSize = (bytes) => {
                if (!bytes) return "0 Б";
                if (bytes < 1024) return bytes + " Б";
                if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " КБ";
                return (bytes / (1024 * 1024)).toFixed(1) + " МБ";
            };
            const addTile = (tile, iconOrThumb, name, sizeStr, removeBtn) => {
                tile.appendChild(iconOrThumb);
                const info = document.createElement("div");
                info.className = "file-preview-tile-info";
                const nameSpan = document.createElement("span");
                nameSpan.className = "file-preview-tile-name";
                nameSpan.textContent = name.length > 50 ? name.slice(0, 47) + "…" : name;
                nameSpan.title = name;
                const sizeSpan = document.createElement("span");
                sizeSpan.className = "file-preview-tile-size";
                sizeSpan.textContent = sizeStr ? `(${sizeStr})` : "";
                info.appendChild(nameSpan);
                info.appendChild(sizeSpan);
                tile.appendChild(info);
                tile.appendChild(removeBtn);
                grid.appendChild(tile);
            };
            if (STATE.editingMsgId && Array.isArray(STATE.editingAttachments)) {
                if (STATE.editingAttachments.length === 0) {
                    UI.filePreview.classList.add("hidden");
                    return;
                }
                UI.filePreview.classList.remove("hidden");
                STATE.editingAttachments.forEach((att) => {
                    const tile = document.createElement("div");
                    tile.className = att.type === "image" ? "file-preview-tile file-preview-tile-img" : "file-preview-tile file-preview-tile-file";
                    tile.dataset.attachmentId = att.id;
                    const removeBtn = document.createElement("button");
                    removeBtn.type = "button";
                    removeBtn.className = "file-preview-tile-remove";
                    removeBtn.title = "Удалить из сообщения";
                    removeBtn.textContent = "×";
                    removeBtn.onclick = (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        STATE.editingAttachmentsToDelete.push(att.id);
                        STATE.editingAttachments = STATE.editingAttachments.filter((a) => a.id !== att.id);
                        this.renderFilePreviewGrid();
                    };
                    if (att.type === "image") {
                        const thumb = document.createElement("div");
                        thumb.className = "file-preview-tile-thumb";
                        thumb.title = "Открыть для просмотра";
                        const img = document.createElement("img");
                        img.alt = att.name;
                        img.src = att.src;
                        thumb.appendChild(img);
                        thumb.onclick = () => {
                            if (this.gallery) this.gallery.openWithUrls([att.src], 0);
                            else window.open(att.src, "_blank");
                        };
                        addTile(tile, thumb, att.name || "Изображение", att.size || null, removeBtn);
                    } else {
                        const ext = (att.name && att.name.includes(".")) ? att.name.split(".").pop().toLowerCase() : "";
                        const iconBox = document.createElement("div");
                        iconBox.className = "file-preview-tile-icon " + getFileIconClass(ext);
                        iconBox.textContent = (att.name && att.name.includes(".")) ? att.name.split(".").pop().toUpperCase() : "Файл";
                        addTile(tile, iconBox, att.name || "Файл", att.size || null, removeBtn);
                    }
                });
                return;
            }
            const files = STATE.selectedFiles || [];
            if (files.length === 0) {
                UI.filePreview.classList.add("hidden");
                return;
            }
            UI.filePreview.classList.remove("hidden");
            const imageUrls = [];
            files.forEach((file, idx) => {
                const isImg = file.type && file.type.startsWith("image/");
                if (isImg) imageUrls.push(URL.createObjectURL(file));
                const tile = document.createElement("div");
                tile.className = isImg ? "file-preview-tile file-preview-tile-img" : "file-preview-tile file-preview-tile-file";
                tile.dataset.index = idx;
                const removeBtn = document.createElement("button");
                removeBtn.type = "button";
                removeBtn.className = "file-preview-tile-remove";
                removeBtn.title = "Открепить";
                removeBtn.textContent = "×";
                removeBtn.onclick = (ev) => {
                    ev.preventDefault();
                    ev.stopPropagation();
                    STATE.selectedFiles = STATE.selectedFiles.filter((_, i) => i !== idx);
                    this.renderFilePreviewGrid();
                };
                const name = file.name || "Файл";
                const sizeStr = fmtSize(file.size);
                if (isImg) {
                    const thumb = document.createElement("div");
                    thumb.className = "file-preview-tile-thumb";
                    thumb.title = "Открыть для просмотра";
                    const img = document.createElement("img");
                    img.alt = name;
                    img.loading = "lazy";
                    img.src = imageUrls[imageUrls.length - 1];
                    const imgIndex = imageUrls.length - 1;
                    thumb.appendChild(img);
                    thumb.onclick = () => {
                        if (this.gallery && imageUrls.length) this.gallery.openWithUrls(imageUrls, imgIndex);
                        else window.open(imageUrls[imgIndex], "_blank");
                    };
                    addTile(tile, thumb, name, sizeStr, removeBtn);
                } else {
                    const ext = (file.name && file.name.includes(".")) ? file.name.split(".").pop().toLowerCase() : "";
                    const iconBox = document.createElement("div");
                    iconBox.className = "file-preview-tile-icon " + getFileIconClass(ext);
                    iconBox.textContent = (file.name && file.name.includes(".")) ? file.name.split(".").pop().toUpperCase() : "Файл";
                    addTile(tile, iconBox, name, sizeStr, removeBtn);
                }
            });
        },

        clearFileSelection() {
            if (STATE.editingMsgId && Array.isArray(STATE.editingAttachments) && STATE.editingAttachments.length > 0) {
                STATE.editingAttachmentsToDelete = (STATE.editingAttachmentsToDelete || []).concat(STATE.editingAttachments.map((a) => a.id));
                STATE.editingAttachments = [];
                this.renderFilePreviewGrid();
                return;
            }
            STATE.selectedFile = null;
            STATE.selectedFiles = null;
            UI.fileInput.value = "";
            if (UI.filePreviewGrid) UI.filePreviewGrid.innerHTML = "";
            UI.filePreview.classList.add("hidden");
        },

        async openChat(chatId, name, isOnline) {
            if (STATE.msgPollTimer) clearInterval(STATE.msgPollTimer);
            STATE.currentChatId = chatId;
            STATE.msgsOffset = 0;
            STATE.ticketMode = false;
            STATE.lastMessageISO = null;
            STATE.lastMessageId = null;
            STATE.windowedMode = false;
            STATE.minLoadedId = null;
            STATE.maxLoadedId = null;
            this.clearReplyTo();
            if (UI.loadNewerSentinel) UI.loadNewerSentinel.classList.add("hidden");
            if (UI.scrollToBottomBtn) UI.scrollToBottomBtn.classList.add("hidden");

            // --- МОБИЛЬНАЯ ЛОГИКА ---
            if (App.Utils.isMobile()) {
                document.querySelector('.chat-layout').classList.add('mobile-chat-active');
            }

            UI.infoPanel.classList.remove("open");

            // Добавляем HTML кнопки назад (она сама скроется на десктопе через CSS)
            UI.chatHeader.innerHTML = `
        <button class="back-btn" id="chat-back-btn" title="К списку чатов">
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
        </button>
        <div class="chat-header-info">
            <div class="chat-header-top">
                <a href="/users/${chatId}" target="_blank" class="chat-header-link">${App.Utils.escapeHtml(name)}</a>
            </div>
            <div class="online-status">
                <span class="online-indicator ${isOnline ? 'online' : 'offline'}"></span>
                <span>${isOnline ? "В сети" : "Не в сети"}</span>
            </div>
        </div>`;

            // Вешаем событие на кнопку Назад
            const backBtn = document.getElementById('chat-back-btn');
            if (backBtn) {
                backBtn.onclick = () => {
                    document.querySelector('.chat-layout').classList.remove('mobile-chat-active');
                    STATE.currentChatId = null; // Сбрасываем текущий чат
                    if (STATE.msgPollTimer) clearInterval(STATE.msgPollTimer);
                    // После выхода из чата скрываем его в режиме «только непрочитанные», если он прочитан.
                    if (App.List && typeof App.List.applyUnreadFilter === "function") {
                        App.List.applyUnreadFilter();
                    }
                };
            }

            // Кнопки шапки (Информация / База знаний / Тикет) временно убраны по требованию.
            // Бэкенд и модули App.Tickets/App.Info/KB оставлены без изменений.
            // App.Tickets.insertHeaderButtons();
            UI.messagesList.innerHTML = "";
            UI.inputArea.classList.remove("hidden");
            this.resetInput();

            const hash = (window.location.hash || "").replace(/^#msg-/, "").trim();
            const aroundMsgId = hash && /^\d+$/.test(hash) ? Number(hash) : null;

            if (aroundMsgId) {
                await this.loadMessagesAround(aroundMsgId);
                this.applyMessageLinkHash();
            } else {
                await this.loadMessages(true);
                this.applyMessageLinkHash();
            }
            this.updateChatUrl();
            this.startPolling();

            // Переоцениваем фильтр «только непрочитанные»: предыдущий (уже прочитанный)
            // чат, из которого мы вышли, скрывается; текущий открытый остаётся виден.
            if (App.List && typeof App.List.applyUnreadFilter === "function") {
                App.List.applyUnreadFilter();
            }

            // === ОТМЕТКА ПРОЧТЕНИЯ ЧЕРЕЗ 3 СЕКУНДЫ ===
            setTimeout(() => {
                if (STATE.currentChatId !== chatId) return;

                const unreadElements = UI.messagesList.querySelectorAll('.message.unread');
                const unreadIds = Array.from(unreadElements).map(el => el.dataset.msgId);

                if (unreadIds.length > 0) {
                    // Убираем визуальную метку ДО отправки (для мгновенного UX)
                    unreadElements.forEach(el => el.classList.remove('unread'));

                    // Отправляем запрос и обновляем список чатов
                    this.markRead(unreadIds);
                }
            }, 3000);
        },

        // Загрузка пачки сообщений (история / вверх в обычном режиме / вверх в режиме ответа)
        async loadMessages(initial = false) {
            if (!STATE.currentChatId) return;
            if (STATE.msgsLoading) return;

            const sentinel = UI.loadMoreSentinel;
            if (!initial && sentinel) sentinel.classList.add("loading");
            STATE.msgsLoading = true;

            try {
                const container = UI.messagesContainer;
                const prevScrollHeight = container.scrollHeight;
                const prevScrollTop = container.scrollTop;

                let url;
                if (STATE.windowedMode && !initial) {
                    url = `${App.API_BASE}/${STATE.currentChatId}/messages?before_id=${STATE.minLoadedId}&limit=20`;
                } else {
                    url = `${App.API_BASE}/${STATE.currentChatId}/messages?limit=20&offset=${STATE.msgsOffset}`;
                }
                const r = await fetch(url);
                if (!r.ok) throw new Error("Failed to fetch messages");

                let msgsBatch = await r.json();
                if (STATE.windowedMode && !initial) msgsBatch = msgsBatch.reverse();

                if (msgsBatch.length === 0) {
                    if (initial) UI.messagesList.innerHTML = '<div class="empty-chat">История переписки пуста</div>';
                    if (sentinel) sentinel.classList.add("done");
                    return;
                }

                if (initial) {
                    const newest = msgsBatch[0];
                    STATE.lastMessageId = newest.msg_id;
                    STATE.lastMessageISO = Utils.getISOTimestamp(newest.date_iso || newest.date);
                }
                if (STATE.windowedMode && !initial) {
                    STATE.minLoadedId = Math.min(...msgsBatch.map(m => m.msg_id));
                }

                const fragment = document.createDocumentFragment();
                const unreadIds = [];
                const reversedMsgs = STATE.windowedMode && !initial ? msgsBatch : [...msgsBatch].reverse();
                let lastDateLabel = null;
                const firstChild = !initial ? UI.messagesList.firstChild : null;

                reversedMsgs.forEach(msg => {
                    const label = App.Utils.getDateLabel(msg.date_iso || msg.date);
                    if (label !== lastDateLabel) {
                        lastDateLabel = label;
                        if (label) {
                            const wouldDuplicateFirst = !initial && firstChild && firstChild.classList?.contains("date-divider") && firstChild.textContent.trim() === label.trim();
                            if (!wouldDuplicateFirst) {
                                const divider = document.createElement("div");
                                divider.className = "date-divider";
                                divider.textContent = label;
                                fragment.appendChild(divider);
                            }
                        }
                    }
                    fragment.appendChild(this.createMessageEl(msg));
                    if (Number(msg.answer) === 0 && !msg.has_read) unreadIds.push(msg.msg_id);
                });

                if (initial) {
                    UI.messagesList.innerHTML = "";
                    UI.messagesList.appendChild(fragment);
                    Utils.scrollToBottom(500);
                    setTimeout(() => this.updateScrollToBottomBtn(), 550);
                } else {
                    UI.messagesList.insertBefore(fragment, UI.messagesList.firstChild);
                    this.normalizeDateDividers();
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            const newScrollHeight = container.scrollHeight;
                            container.scrollTop = prevScrollTop + (newScrollHeight - prevScrollHeight);
                        });
                    });
                }

                if (!STATE.windowedMode) STATE.msgsOffset += msgsBatch.length;
                const hasMore = msgsBatch.length >= 20;
                if (sentinel) sentinel.classList.toggle("done", !hasMore);

                if (unreadIds.length > 0) this.markRead(unreadIds);
                if (STATE.ticketMode) App.Tickets.renderCheckboxes();

            } catch (e) {
                console.error("Load messages error:", e);
                DarkToast.error("Ошибка при загрузке сообщений");
            } finally {
                STATE.msgsLoading = false;
                if (sentinel) sentinel.classList.remove("loading");
            }
        },

        /**
         * Удаляет разделители даты, оказавшиеся между двумя сообщениями одного дня
         * (после подгрузки пачки вверх граница дня может дублироваться).
         */
        normalizeDateDividers() {
            if (!UI.messagesList) return;
            const nodes = Array.from(UI.messagesList.children).filter(el =>
                el.classList.contains("date-divider") || el.classList.contains("message")
            );
            const toRemove = [];
            for (let i = 1; i < nodes.length - 1; i++) {
                const node = nodes[i];
                if (node.classList.contains("date-divider")) {
                    const prev = nodes[i - 1];
                    const next = nodes[i + 1];
                    const prevLabel = prev.classList.contains("message") ? prev.dataset.dateLabel : null;
                    const nextLabel = next.classList.contains("message") ? next.dataset.dateLabel : null;
                    if (prevLabel != null && nextLabel != null && prevLabel === nextLabel) toRemove.push(node);
                }
            }
            toRemove.forEach(el => el.remove());
        },

        async loadMessagesAround(aroundMsgId) {
            if (!STATE.currentChatId || STATE.msgsLoading) return;
            STATE.msgsLoading = true;
            const container = UI.messagesContainer;
            try {
                const r = await fetch(`${App.API_BASE}/${STATE.currentChatId}/messages?around_msg_id=${aroundMsgId}`);
                if (!r.ok) throw new Error("Failed");
                const msgs = await r.json();
                if (!msgs.length) return;

                STATE.windowedMode = true;
                STATE.minLoadedId = Math.min(...msgs.map(m => m.msg_id));
                STATE.maxLoadedId = Math.max(...msgs.map(m => m.msg_id));
                if (UI.loadMoreSentinel) UI.loadMoreSentinel.classList.remove("done");
                if (UI.loadNewerSentinel) {
                    UI.loadNewerSentinel.classList.remove("hidden");
                    UI.loadNewerSentinel.classList.remove("loading");
                }

                UI.messagesList.innerHTML = "";
                const fragment = document.createDocumentFragment();
                let lastDateLabel = null;
                msgs.forEach(msg => {
                    const label = App.Utils.getDateLabel(msg.date_iso || msg.date);
                    if (label !== lastDateLabel) {
                        lastDateLabel = label;
                        if (label) {
                            const divider = document.createElement("div");
                            divider.className = "date-divider";
                            divider.textContent = label;
                            fragment.appendChild(divider);
                        }
                    }
                    fragment.appendChild(this.createMessageEl(msg));
                });
                UI.messagesList.appendChild(fragment);

                requestAnimationFrame(() => {
                    const el = document.getElementById("msg-" + aroundMsgId);
                    if (el) {
                        el.scrollIntoView({ behavior: "smooth", block: "center" });
                        el.classList.add("message-highlight");
                        setTimeout(() => el.classList.remove("message-highlight"), 2000);
                    }
                });
                this.setupLoadNewerObserver();
                this.updateScrollToBottomBtn();
                // Одна подгрузка вверх сразу, чтобы при первом скролле вверх контент уже был
                setTimeout(() => {
                    if (STATE.windowedMode && !STATE.msgsLoading && STATE.currentChatId) this.loadMessages(false);
                }, 400);
            } catch (e) {
                console.error("loadMessagesAround error:", e);
                DarkToast.error("Не удалось загрузить сообщения");
            } finally {
                STATE.msgsLoading = false;
            }
        },

        async loadMessagesNewer() {
            if (!STATE.currentChatId || STATE.msgsLoading || STATE.maxLoadedId == null) return;
            STATE.msgsLoading = true;
            const newerSentinel = UI.loadNewerSentinel;
            if (newerSentinel) newerSentinel.classList.add("loading");
            try {
                const r = await fetch(`${App.API_BASE}/${STATE.currentChatId}/messages?after_id=${STATE.maxLoadedId}&limit=20`);
                if (!r.ok) throw new Error("Failed");
                let msgs = await r.json();
                if (msgs.length === 0) {
                    if (newerSentinel) newerSentinel.classList.add("hidden");
                    return;
                }
                STATE.maxLoadedId = Math.max(...msgs.map(m => m.msg_id));
                msgs = msgs.reverse();
                const messagesInList = UI.messagesList.querySelectorAll(".message");
                const lastMsgInList = messagesInList.length ? messagesInList[messagesInList.length - 1] : null;
                let lastDateLabel = lastMsgInList && lastMsgInList.dataset.dateLabel ? lastMsgInList.dataset.dateLabel : null;
                const fragment = document.createDocumentFragment();
                msgs.forEach(msg => {
                    if (document.getElementById("msg-" + msg.msg_id)) return;
                    const label = App.Utils.getDateLabel(msg.date_iso || msg.date);
                    if (label !== lastDateLabel) {
                        lastDateLabel = label;
                        if (label) {
                            const divider = document.createElement("div");
                            divider.className = "date-divider";
                            divider.textContent = label;
                            fragment.appendChild(divider);
                        }
                    }
                    fragment.appendChild(this.createMessageEl(msg));
                });
                const newUrls = Array.from(fragment.querySelectorAll('.message-image-thumb, .message-image')).filter(img => img.style.display !== 'none').map(img => img.src);
                if (fragment.childNodes.length) UI.messagesList.appendChild(fragment);
                if (newUrls.length && this.gallery) this.gallery.prependToGallery(newUrls);
                if (msgs.length < 20 && newerSentinel) newerSentinel.classList.add("hidden");
                this.updateScrollToBottomBtn();
            } catch (e) {
                console.error("loadMessagesNewer error:", e);
            } finally {
                STATE.msgsLoading = false;
                if (newerSentinel) newerSentinel.classList.remove("loading");
            }
        },

        setupLoadNewerObserver() {
            if (!UI.loadNewerSentinel || !UI.messagesContainer) return;
            if (this._loadNewerObserver) this._loadNewerObserver.disconnect();
            this._loadNewerObserver = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (!entry.isIntersecting || !STATE.windowedMode || STATE.msgsLoading) return;
                        if (UI.loadNewerSentinel.classList.contains("hidden")) return;
                        this.loadMessagesNewer();
                    });
                },
                { root: UI.messagesContainer, rootMargin: "0px 0px 200px 0px", threshold: 0 }
            );
            this._loadNewerObserver.observe(UI.loadNewerSentinel);
        },

        updateScrollToBottomBtn() {
            const btn = UI.scrollToBottomBtn;
            const cont = UI.messagesContainer;
            if (!btn || !cont) return;
            const gap = cont.scrollHeight - cont.scrollTop - cont.clientHeight;
            const atBottom = gap <= 50;
            if (atBottom) {
                btn.classList.add("hidden");
                btn.classList.remove("has-new-below");
            } else {
                btn.classList.remove("hidden");
            }
        },

        scrollToBottom() {
            const cont = UI.messagesContainer;
            if (!cont) return;
            const go = () => { cont.scrollTop = cont.scrollHeight; };
            go();
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    go();
                    setTimeout(go, 80);
                });
            });
            if (UI.scrollToBottomBtn) {
                UI.scrollToBottomBtn.classList.add("hidden");
                UI.scrollToBottomBtn.classList.remove("has-new-below");
            }
        },

        setupLoadMoreObserver() {
            if (!UI.loadMoreSentinel || !UI.messagesContainer) return;
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (!entry.isIntersecting) return;
                        if (STATE.msgsLoading) return;
                        if (UI.loadMoreSentinel && UI.loadMoreSentinel.classList.contains("done")) return;
                        this.loadMessages(false);
                    });
                },
                { root: UI.messagesContainer, rootMargin: "100px 0px 0px 0px", threshold: 0 }
            );
            observer.observe(UI.loadMoreSentinel);
        },

        updateChatUrl() {
            if (!STATE.currentChatId) return;
            const url = `${window.location.pathname}?chat=${STATE.currentChatId}${window.location.hash || ""}`;
            if (window.location.pathname + window.location.search + window.location.hash !== url) {
                window.history.replaceState(null, "", url);
            }
        },

        applyMessageLinkHash() {
            const hash = (window.location.hash || "").replace(/^#msg-/, "");
            if (!hash || !STATE.currentChatId) return;
            const el = document.getElementById("msg-" + hash);
            if (!el || !UI.messagesList.contains(el)) return;
            requestAnimationFrame(() => {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
                el.classList.add("message-highlight");
                setTimeout(() => el.classList.remove("message-highlight"), 2000);
            });
        },

        setReplyTo(msgId, author, text) {
            STATE.replyToMsgId = msgId;
            if (UI.replyStrip) UI.replyStrip.classList.remove("hidden");
            if (UI.replyAuthor) UI.replyAuthor.textContent = author || "Сообщение";
            if (UI.replyText) UI.replyText.textContent = text ? " — " + String(text).slice(0, 80) : "";
            UI.input?.focus();
        },

        clearReplyTo() {
            STATE.replyToMsgId = null;
            if (UI.replyStrip) UI.replyStrip.classList.add("hidden");
            if (UI.replyAuthor) UI.replyAuthor.textContent = "";
            if (UI.replyText) UI.replyText.textContent = "";
        },

        bindContextMenu() {
            const menu = UI.messageContextMenu;
            if (!menu) return;
            let contextMenuMessageEl = null;
            let anchorOffsetX = 0;
            let anchorOffsetY = 0;

            const closeMenu = () => {
                menu.classList.add("hidden");
                contextMenuMessageEl = null;
            };

            const positionMenu = () => {
                if (!contextMenuMessageEl || menu.classList.contains("hidden")) return;
                const msgRect = contextMenuMessageEl.getBoundingClientRect();
                const x = msgRect.left + anchorOffsetX;
                const y = msgRect.top + anchorOffsetY;
                const menuRect = menu.getBoundingClientRect();
                menu.style.left = Math.max(8, Math.min(x, window.innerWidth - menuRect.width - 8)) + "px";
                menu.style.top = Math.max(8, Math.min(y, window.innerHeight - menuRect.height - 8)) + "px";
            };

            UI.messagesList.addEventListener("contextmenu", (e) => {
                const msg = e.target.closest(".message");
                if (!msg || !msg.dataset.msgId) return;
                e.preventDefault();
                e.stopPropagation();
                contextMenuMessageEl = msg;
                const msgRect = msg.getBoundingClientRect();
                anchorOffsetX = e.clientX - msgRect.left;
                anchorOffsetY = e.clientY - msgRect.top;
                const isOwn = msg.classList.contains("you") && msg.classList.contains("own");
                const canDelete = isOwn || (window.PRIVILEGED && msg.classList.contains("you"));
                const textEl = msg.querySelector(".text");
                const hasText = textEl && (textEl.textContent || "").trim().length > 0;

                menu.querySelector(".ctx-edit").classList.toggle("hidden", !isOwn);
                menu.querySelector(".ctx-delete").classList.toggle("hidden", !canDelete);
                menu.querySelector(".ctx-copy").classList.toggle("hidden", !hasText);

                menu.classList.remove("hidden");
                positionMenu();
            });

            window.addEventListener("resize", positionMenu);

            document.addEventListener("click", (e) => {
                if (!menu.classList.contains("hidden") && !menu.contains(e.target)) closeMenu();
            });
            document.addEventListener("contextmenu", (e) => {
                if (!menu.classList.contains("hidden") && !menu.contains(e.target)) closeMenu();
            });
            document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

            menu.querySelectorAll(".ctx-item").forEach((btn) => {
                btn.addEventListener("click", (e) => {
                    const msg = contextMenuMessageEl;
                    closeMenu();
                    if (!msg) return;
                    const action = e.currentTarget.dataset.action;
                    if (action === "reply") {
                        this.setReplyTo(
                            msg.dataset.msgId,
                            msg.dataset.replyAuthor || "",
                            msg.dataset.replySnippet || ""
                        );
                    } else if (action === "copy") {
                        const t = (msg.querySelector(".text")?.textContent || "").trim();
                        if (t) navigator.clipboard.writeText(t).then(() => DarkToast.success("Скопировано")).catch(() => {});
                    } else if (action === "edit") {
                        STATE.editingMsgId = msg.dataset.msgId;
                        const textEl = msg.querySelector(".message-text") || msg.querySelector(".text");
                        if (UI.input && textEl) this.setEditorHtml(textEl.innerHTML.trim() || "");
                        const bubble = msg.querySelector(".message-bubble");
                        const editAttachments = [];
                        if (bubble) {
                            bubble.querySelectorAll(".message-image-cell[data-attachment-id]").forEach(cell => {
                                const id = cell.getAttribute("data-attachment-id");
                                if (!id) return;
                                const img = cell.querySelector(".message-image");
                                editAttachments.push({ id, type: "image", name: "Изображение", src: img ? img.src : "", size: null });
                            });
                            bubble.querySelectorAll(".message-file-link[data-attachment-id]").forEach(link => {
                                const id = link.getAttribute("data-attachment-id");
                                if (!id) return;
                                const name = link.getAttribute("download") || link.querySelector(".file-link-name")?.getAttribute("title") || "Файл";
                                const sizeEl = link.querySelector(".file-size-mb");
                                editAttachments.push({ id, type: "file", name, href: link.href, size: sizeEl ? sizeEl.textContent : null });
                            });
                        }
                        STATE.editingAttachments = editAttachments;
                        STATE.editingAttachmentsToDelete = [];
                        if (editAttachments.length > 0) this.renderFilePreviewGrid();
                        UI.cancelEditBtn.classList.remove("hidden");
                        UI.input?.focus();
                    } else if (action === "delete") {
                        this.confirmDelete(msg);
                    }
                });
            });
        },

        // Создание HTML-элемента сообщения
        createMessageEl(msg) {
            const div = document.createElement("div");
            const answerVal = Number(msg.answer);
            const userIdVal = Number(msg.user_id);
            const currentUserIdVal = Number(window.CURRENT_USER_ID);

            // Логика сторон: 0 - клиент (слева), 1 - поддержка (справа)
            const isSupport = answerVal === 1;
            const isOwn = isSupport && userIdVal === currentUserIdVal;

            let messageClass = isSupport ? 'you' : 'other';
            if (isOwn) messageClass += ' own';
            if (STATE.ticketMode && !isSupport) messageClass += ' ticket-offset';

            // Добавляем класс 'unread' для непрочитанных входящих сообщений
            if (answerVal === 0 && !msg.has_read) {
                messageClass += ' unread';
            }

            div.id = "msg-" + msg.msg_id;
            div.className = `message ${messageClass}`;
            div.dataset.msgId = msg.msg_id;
            div.dataset.replyAuthor = App.Utils.escapeHtml(msg.whose_message || "");
            div.dataset.replySnippet = String(msg.text || "").trim().slice(0, 80);
            div.dataset.readFromTable = (msg.read_from_table === true || msg.read_from_table === "true") ? "1" : "0";

            const dateLabel = App.Utils.getDateLabel(msg.date_iso || msg.date);
            if (dateLabel) div.dataset.dateLabel = dateLabel;

            const imageExts = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"];
            const extToLabel = { ".pdf": "PDF", ".xlsx": "XLS", ".xls": "XLS", ".doc": "DOC", ".docx": "DOC", ".docm": "DOC", ".txt": "TXT", ".csv": "CSV", ".zip": "ZIP" };
            const attachments = msg.attachments || [];
            const imageItems = [];
            const legacyImagePath = msg.file_path || msg.file_new || null;
            if (legacyImagePath && String(legacyImagePath).trim() !== "") {
                const legacyHref = (String(legacyImagePath).startsWith("/")) ? legacyImagePath : ("/" + String(legacyImagePath).replace(/^\/+/, ""));
                imageItems.push({ href: legacyHref, id: null });
            }
            attachments.forEach(att => {
                const ext = (att.file_ext || "").toLowerCase();
                if (imageExts.includes(ext)) {
                    const href = (att.file_path && att.file_path.startsWith("/")) ? att.file_path : ("/" + (att.file_path || "").replace(/^\/+/, ""));
                    imageItems.push({ href, id: att.id != null ? att.id : null });
                }
            });
            const fileAttachments = attachments.filter(att => !imageExts.includes((att.file_ext || "").toLowerCase()));

            let imagesBlock = "";
            if (imageItems.length > 0) {
                imagesBlock = '<div class="message-images-grid">';
                imageItems.forEach(({ href, id }) => {
                    const dataId = id != null ? ` data-attachment-id="${id}"` : "";
                    imagesBlock += `<div class="message-image-cell"${dataId}><img src="${href}" class="message-image message-image-thumb" loading="lazy" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='block'; this.parentElement.classList.add('image-load-failed');"><div class="img-disappeared" style="display:none;">Картинка потерялась</div></div>`;
                });
                imagesBlock += "</div>";
            }

            const FILE_TYPE_MAP = {
                pdf: { label: "PDF", cls: "file-type-pdf" },
                doc: { label: "DOC", cls: "file-type-doc" },
                docx: { label: "WORD", cls: "file-type-doc" },
                docm: { label: "WORD", cls: "file-type-doc" },
                xls: { label: "XLS", cls: "file-type-xlsx" },
                xlsx: { label: "XLSX", cls: "file-type-xlsx" },
                csv: { label: "CSV", cls: "file-type-csv" },
                txt: { label: "TXT", cls: "file-type-txt" },
                css: { label: "CSS", cls: "file-type-css" },
                html: { label: "HTML", cls: "file-type-html" },
                htm: { label: "HTML", cls: "file-type-html" },
                xml: { label: "XML", cls: "file-type-xml" },
                json: { label: "JSON", cls: "file-type-json" },
                zip: { label: "ZIP", cls: "file-type-zip" },
                rar: { label: "RAR", cls: "file-type-zip" }
            };
            let filesBlock = "";
            if (fileAttachments.length > 0) {
                filesBlock = '<div class="message-file-links">';
                const maxNameLen = 22;
                fileAttachments.forEach(att => {
                    const extRaw = (att.file_ext || "").toLowerCase().replace(/^\./, "");
                    const extFromName = (att.original_filename || "").split(".").pop()?.toLowerCase() || "";
                    const ext = extRaw || extFromName;
                    const name = att.original_filename || "Файл";
                    const displayName = name.length > maxNameLen
                        ? name.slice(0, Math.max(0, maxNameLen - 4 - (ext ? ext.length + 1 : 0))) + "…" + (ext ? "." + ext : "")
                        : name;
                    const badge = FILE_TYPE_MAP[ext] || { label: (ext || "FILE").toUpperCase().slice(0, 4), cls: "file-type-default" };
                    const href = (att.file_path && att.file_path.startsWith("/")) ? att.file_path : ("/" + (att.file_path || "").replace(/^\/+/, ""));
                    const sizeStr = att.file_size_bytes != null
                        ? (att.file_size_bytes < 1024 ? att.file_size_bytes + " Б" : att.file_size_bytes < 1024 * 1024 ? (att.file_size_bytes / 1024).toFixed(1) + " КБ" : (att.file_size_bytes / (1024 * 1024)).toFixed(1) + " МБ")
                        : "";
                    const sizeHtml = sizeStr ? `<span class="file-size-mb">${sizeStr}</span>` : "";
                    const attId = att.id != null ? ` data-attachment-id="${att.id}"` : "";
                    filesBlock += `<a class="message-file-link" href="${href}" download="${App.Utils.escapeHtml(name)}" target="_blank" rel="noopener"${attId}><span class="file-type-badge ${badge.cls}">${App.Utils.escapeHtml(badge.label)}</span><span class="file-link-wrapper"><span class="file-link-name" title="${App.Utils.escapeHtml(name)}">${App.Utils.escapeHtml(displayName)}</span>${sizeHtml}</span></a>`;
                });
                filesBlock += "</div>";
            }

            const replyBlock = (msg.relay_msg_id && String(msg.relay_msg_id).trim()) ? `
        <div class="message-reply-to" data-reply-to-msg-id="${msg.relay_msg_id}" role="button" tabindex="0" title="Перейти к сообщению">
            <span class="reply-to-author">${App.Utils.escapeHtml(msg.relay_author || "Сообщение")}</span>
            ${msg.relay_snippet ? `<span class="reply-to-text">${App.Utils.escapeHtml(App.Utils.plainTextReplySnippet(msg.relay_snippet, 80))}</span>` : ""}
        </div>` : '';

            const isYou = messageClass.includes('you');
            const hasRead = !!(msg.has_read === true || msg.has_read === 'true' || msg.has_read === 1 || msg.has_read === '1' || String(msg.has_read).toLowerCase() === 'true');
            const readReceiptHtml = isYou ? `
                <span class="message-read-receipt ${hasRead ? 'read' : ''}" data-msg-id="${msg.msg_id}" data-has-read="${hasRead}">
                    <svg class="message-read-receipt-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
                    ${hasRead ? `<svg class="message-read-receipt-icon second" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>` : ''}
                </span>` : '';

            const textBlock = (msg.text && String(msg.text).trim()) ? `<div class="message-text">${typeof window.sanitizeMessageHtml === "function" ? window.sanitizeMessageHtml(msg.text) : App.Utils.escapeHtml(msg.text)}</div>` : "";
            div.innerHTML = `
        <div class="message-unread-marker"></div>
        <div class="message-bubble">
            ${replyBlock}
            ${imagesBlock}
            ${filesBlock}
            ${textBlock}
            <div class="message-meta">
                <span class="whose-message">${App.Utils.escapeHtml(msg.whose_message)}</span>
                <span class="time">${App.Utils.formatDateTime(msg.date_iso || msg.date)}</span>
                ${readReceiptHtml}
            </div>
        </div>`;

            if (isYou) this.bindReadReceiptHover(div);
            return div;
        },

        bindReadReceiptHover(messageEl) {
            const receipt = messageEl.querySelector('.message-read-receipt');
            if (!receipt) return;
            if (!receipt.classList.contains('read')) return;
            let popover = document.getElementById('chat-reads-popover');
            if (!popover) {
                popover = document.createElement('div');
                popover.id = 'chat-reads-popover';
                popover.className = 'message-reads-popover hidden';
                document.body.appendChild(popover);
            }
            let hideTimer = null;
            const container = UI.messagesList ? UI.messagesList.closest('.chat-messages-wrap') : null;

            const formatReadTime = (s) => {
                if (!s) return '';
                const d = new Date(s);
                if (isNaN(d.getTime())) return String(s);
                const day = String(d.getDate()).padStart(2, '0');
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const year = d.getFullYear();
                const h = String(d.getHours()).padStart(2, '0');
                const min = String(d.getMinutes()).padStart(2, '0');
                return `${day}.${month}.${year}, ${h}:${min}`;
            };

            const show = (list) => {
                if (!list || list.length === 0) {
                    popover.innerHTML = '<div class="message-reads-popover-empty">Нет данных о прочтении</div>';
                } else {
                    popover.innerHTML = list.map(r =>
                        `<div class="message-reads-popover-row"><span class="name">${App.Utils.escapeHtml(r.display_name)}</span><span class="read-time">${App.Utils.escapeHtml(formatReadTime(r.read_time))}</span></div>`
                    ).join('');
                }
                popover.classList.remove('hidden');
                const rect = receipt.getBoundingClientRect();
                let left = rect.left;
                let top = rect.top - 8;

                if (container) {
                    const cr = container.getBoundingClientRect();
                    const pw = popover.offsetWidth || 260;
                    const ph = popover.offsetHeight || 80;
                    left = Math.max(cr.left, Math.min(left, cr.right - pw));
                    top = rect.top - ph - 8;
                    if (top < cr.top) top = rect.bottom + 8;
                    top = Math.max(cr.top, Math.min(top, cr.bottom - ph));
                } else {
                    const pw = popover.offsetWidth || 260;
                    const ph = popover.offsetHeight || 80;
                    left = Math.min(left, window.innerWidth - pw);
                    top = rect.top - ph - 8;
                }

                popover.style.left = `${left}px`;
                popover.style.top = `${top}px`;
                popover.style.transform = '';
            };
            const hide = () => {
                hideTimer = setTimeout(() => popover.classList.add('hidden'), 100);
            };
            receipt.addEventListener('mouseenter', async () => {
                if (hideTimer) clearTimeout(hideTimer);
                const msgId = receipt.dataset.msgId;
                if (!msgId || !STATE.currentChatId) return;
                try {
                    const r = await fetch(`${App.API_BASE}/${STATE.currentChatId}/messages/${msgId}/reads`, { credentials: 'include' });
                    const data = r.ok ? await r.json() : { reads: [] };
                    show(data.reads || []);
                } catch (e) {
                    show([]);
                }
            });
            receipt.addEventListener('mouseleave', () => hide());
            popover.addEventListener('mouseenter', () => { if (hideTimer) clearTimeout(hideTimer); });
            popover.addEventListener('mouseleave', () => hide());
        },

        // Отправка (новое или редактируемое)
        async handleSend() {
            const rawHtml = this.getEditorHtml();
            const text = (typeof window.sanitizeMessageHtml === "function" ? window.sanitizeMessageHtml(rawHtml) : rawHtml);
            const hasText = UI.input && (UI.input.textContent || "").trim().length > 0;
            const hasFiles = (STATE.selectedFiles && STATE.selectedFiles.length > 0) || STATE.selectedFile;
            const hasEditDeletes = STATE.editingMsgId && STATE.editingAttachmentsToDelete && STATE.editingAttachmentsToDelete.length > 0;
            if (!hasText && !hasFiles && !hasEditDeletes) return;

            UI.sendBtn.disabled = true;
            try {
                if (STATE.editingMsgId) {
                    const msgId = STATE.editingMsgId;
                    const toDelete = STATE.editingAttachmentsToDelete || [];
                    const remainingAttachments = STATE.editingAttachments || [];
                    for (const attId of toDelete) {
                        await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages/${msgId}/attachments/${attId}`, { method: "DELETE" });
                    }
                    const willBeEmpty = !text && remainingAttachments.length === 0;
                    if (willBeEmpty) {
                        const res = await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages/${msgId}`, { method: "DELETE" });
                        if (res.ok) {
                            const msgEl = document.getElementById("msg-" + msgId);
                            if (msgEl) {
                                const dateLabel = msgEl.dataset.dateLabel;
                                msgEl.remove();
                                if (dateLabel) {
                                    const remaining = UI.messagesList.querySelectorAll(`.message[data-date-label="${CSS.escape(dateLabel)}"]`);
                                    if (remaining.length === 0) {
                                        const divider = Array.from(UI.messagesList.querySelectorAll(".date-divider")).find((d) => d.textContent === dateLabel);
                                        if (divider) divider.remove();
                                    }
                                }
                            }
                            this.resetInput();
                            DarkToast.success("Сообщение удалено");
                        }
                    } else {
                        const res = await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages/${msgId}`, {
                            method: "PUT",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ text })
                        });
                        if (res.ok) {
                            const msgEl = document.getElementById("msg-" + msgId);
                            if (msgEl) {
                                toDelete.forEach((attId) => {
                                    const el = msgEl.querySelector(`[data-attachment-id="${attId}"]`);
                                    if (el) el.remove();
                                });
                                const grid = msgEl.querySelector(".message-images-grid");
                                if (grid && grid.children.length === 0) grid.remove();
                                const fileLinks = msgEl.querySelector(".message-file-links");
                                if (fileLinks && fileLinks.children.length === 0) fileLinks.remove();
                                const textEl = msgEl.querySelector(".message-text") || msgEl.querySelector(".text");
                                if (textEl) {
                                    if (text) textEl.innerHTML = typeof window.sanitizeMessageHtml === "function" ? window.sanitizeMessageHtml(text) : App.Utils.escapeHtml(text);
                                    else textEl.remove();
                                }
                            }
                            this.resetInput();
                            DarkToast.success("Сообщение изменено");
                        }
                    }
                } else {
                    const allFiles = STATE.selectedFiles && STATE.selectedFiles.length > 0
                        ? STATE.selectedFiles
                        : (STATE.selectedFile ? [STATE.selectedFile] : []);
                    const files = allFiles.slice(0, MAX_FILES_PER_MESSAGE);
                    if (allFiles.length > MAX_FILES_PER_MESSAGE) {
                        DarkToast.info("Прикреплено только первые " + MAX_FILES_PER_MESSAGE + " файлов.");
                    }
                    const wrap = UI.uploadProgressWrap;
                    const fill = UI.uploadProgressFill;
                    const fn = UI.uploadFilesN;
                    const ft = UI.uploadFilesTotal;
                    const mn = UI.uploadMbN;
                    const mt = UI.uploadMbTotal;
                    const speedEl = UI.uploadSpeed;
                    const chunks = [];
                    for (let i = 0; i < files.length; i += MAX_FILES_PER_MESSAGE) {
                        chunks.push(files.slice(i, i + MAX_FILES_PER_MESSAGE));
                    }
                    let m;
                    if (files.length > 0) {
                        const totalFiles = files.length;
                        const totalSize = files.reduce((s, f) => s + (f.size || 0), 0);
                        const totalMb = (totalSize / (1024 * 1024)).toFixed(1);
                        const uploadStartTime = Date.now();
                        if (wrap) wrap.classList.remove("hidden");
                        if (speedEl) speedEl.textContent = "";
                        if (mt) mt.textContent = totalMb;
                        if (ft) ft.textContent = String(totalFiles);
                        let uploadedCount = 0;
                        let uploadedSize = 0;
                        for (let c = 0; c < chunks.length; c++) {
                            const chunk = chunks[c];
                            const fd = new FormData();
                            fd.append("text", c === 0 ? (text || " ") : " ");
                            if (c === 0 && STATE.replyToMsgId) {
                                fd.append("relay_msg_id", String(STATE.replyToMsgId));
                                const author = (UI.replyAuthor && UI.replyAuthor.textContent) ? UI.replyAuthor.textContent.trim() : "";
                                const snippetRaw = (UI.replyText && UI.replyText.textContent) ? UI.replyText.textContent : "";
                                const snippet = snippetRaw.replace(/^\s*—\s*/, "").trim().slice(0, 80);
                                if (author) fd.append("relay_author", author);
                                if (snippet) fd.append("relay_snippet", snippet);
                            }
                            const rCreate = await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages`, { method: "POST", body: fd });
                            if (!rCreate.ok) throw new Error("Не удалось создать сообщение");
                            m = await rCreate.json();
                            if (c === 0) {
                                STATE.lastMessageId = m.msg_id;
                                STATE.lastMessageISO = Utils.getISOTimestamp(m.date_iso || m.date);
                            }
                            const chunkSize = chunk.reduce((s, f) => s + (f.size || 0), 0);
                            const attachments = [];
                            for (let i = 0; i < chunk.length; i++) {
                                if (fn) fn.textContent = String(uploadedCount + i);
                                const form = new FormData();
                                form.append("file", chunk[i]);
                                const xhr = new XMLHttpRequest();
                                await new Promise((resolve, reject) => {
                                    xhr.open("POST", `${App.API_BASE}/${STATE.currentChatId}/messages/${m.msg_id}/attachments`);
                                    xhr.withCredentials = true;
                                    xhr.onload = () => {
                                        uploadedSize += chunk[i].size || 0;
                                        uploadedCount++;
                                        if (fn) fn.textContent = String(uploadedCount);
                                        if (mn) mn.textContent = (uploadedSize / (1024 * 1024)).toFixed(1);
                                        if (fill) fill.style.width = totalSize ? (100 * uploadedSize / totalSize) + "%" : "100%";
                                        if (xhr.status >= 200 && xhr.status < 300) {
                                            try {
                                                attachments.push(JSON.parse(xhr.responseText));
                                            } catch (err) {}
                                            resolve();
                                        } else reject(new Error(xhr.statusText || "Ошибка загрузки"));
                                    };
                                    xhr.onerror = () => reject(new Error("Ошибка сети"));
                                    xhr.upload.onprogress = (ev) => {
                                        const loaded = uploadedSize + (ev.loaded || 0);
                                        if (mn) mn.textContent = (loaded / (1024 * 1024)).toFixed(1);
                                        if (fill) fill.style.width = totalSize ? (100 * loaded / totalSize) + "%" : "100%";
                                        if (speedEl) {
                                            const elapsed = (Date.now() - uploadStartTime) / 1000;
                                            if (elapsed > 0.2) {
                                                const speedBps = loaded / elapsed;
                                                speedEl.textContent = (speedBps / (1024 * 1024)).toFixed(1) + " МБ/с";
                                            }
                                        }
                                    };
                                    xhr.send(form);
                                });
                            }
                            m.attachments = attachments;
                            this.clearReplyTo();
                            let needDivider = false;
                            const lastChild = UI.messagesList.lastElementChild;
                            if (!lastChild || !lastChild.classList.contains("date-divider")) {
                                const todayLabel = App.Utils.getDateLabel(new Date().toISOString());
                                const existingDividers = UI.messagesList.querySelectorAll(".date-divider");
                                const hasToday = Array.from(existingDividers).some(d => d.textContent === todayLabel);
                                if (!hasToday) needDivider = true;
                            }
                            if (needDivider && c === 0) {
                                const divider = document.createElement("div");
                                divider.className = "date-divider";
                                divider.textContent = App.Utils.getDateLabel(new Date().toISOString());
                                UI.messagesList.appendChild(divider);
                            }
                            UI.messagesList.appendChild(this.createMessageEl(m));
                            STATE.lastMessageId = m.msg_id;
                            STATE.lastMessageISO = Utils.getISOTimestamp(m.date_iso || m.date);
                            const el = document.getElementById("msg-" + m.msg_id);
                            const urls = el ? Array.from(el.querySelectorAll('.message-image-thumb, .message-image')).filter(img => img.style.display !== 'none').map(img => img.src) : [];
                            if (urls.length && this.gallery) this.gallery.prependToGallery(urls);
                        }
                        if (wrap) wrap.classList.add("hidden");
                        if (fill) fill.style.width = "0%";
                        if (speedEl) speedEl.textContent = "";
                    } else {
                        const fd = new FormData();
                        fd.append("text", text);
                        if (STATE.replyToMsgId) {
                            fd.append("relay_msg_id", String(STATE.replyToMsgId));
                            const author = (UI.replyAuthor && UI.replyAuthor.textContent) ? UI.replyAuthor.textContent.trim() : "";
                            const snippetRaw = (UI.replyText && UI.replyText.textContent) ? UI.replyText.textContent : "";
                            const snippet = snippetRaw.replace(/^\s*—\s*/, "").trim().slice(0, 80);
                            if (author) fd.append("relay_author", author);
                            if (snippet) fd.append("relay_snippet", snippet);
                        }
                        const r = await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages`, { method: "POST", body: fd });
                        if (!r.ok) throw new Error("Ошибка отправки");
                        m = await r.json();
                    }

                    if (files.length === 0) {
                        this.clearReplyTo();
                        let needDivider = false;
                        const lastChild = UI.messagesList.lastElementChild;
                        if (!lastChild || !lastChild.classList.contains("date-divider")) {
                            const todayLabel = App.Utils.getDateLabel(new Date().toISOString());
                            const existingDividers = UI.messagesList.querySelectorAll(".date-divider");
                            const hasToday = Array.from(existingDividers).some(d => d.textContent === todayLabel);
                            if (!hasToday) needDivider = true;
                        }
                        if (needDivider) {
                            const divider = document.createElement("div");
                            divider.className = "date-divider";
                            divider.textContent = App.Utils.getDateLabel(new Date().toISOString());
                            UI.messagesList.appendChild(divider);
                        }
                        UI.messagesList.appendChild(this.createMessageEl(m));
                        STATE.lastMessageId = m.msg_id;
                        STATE.lastMessageISO = Utils.getISOTimestamp(m.date_iso || m.date);
                        const el = document.getElementById("msg-" + m.msg_id);
                        const urls = el ? Array.from(el.querySelectorAll('.message-image-thumb, .message-image')).filter(img => img.style.display !== 'none').map(img => img.src) : [];
                        if (urls.length && this.gallery) this.gallery.prependToGallery(urls);
                    }
                    Utils.scrollToBottom(200);
                    this.resetInput();
                    if (App.List) App.List.moveChatToTop(STATE.currentChatId);
                }
            } catch (e) {
                DarkToast.error("Не удалось отправить сообщение");
            } finally {
                UI.sendBtn.disabled = false;
            }
        },

        handleListClick(e) {
            if (e.target.classList.contains("message-image") || e.target.classList.contains("message-image-thumb")) {
                this.gallery.open(e.target.src || e.target.getAttribute("src"));
                return;
            }
            const replyBlock = e.target.closest(".message-reply-to");
            if (replyBlock && replyBlock.dataset.replyToMsgId) {
                e.preventDefault();
                this.loadMessagesAround(Number(replyBlock.dataset.replyToMsgId));
            }
        },

        // Модальное подтверждение удаления
        async confirmDelete(msgEl) {
            UI.deleteModal.classList.add("visible");
            const confirmBtn = UI.deleteModal.querySelector(".delete-confirm-btn");

            // Очистка старых событий клонированием узла
            const newBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

            newBtn.onclick = async () => {
                const msgId = msgEl.dataset.msgId;
                const dateLabel = msgEl.dataset.dateLabel;

                try {
                    const r = await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages/${msgId}`, { method: "DELETE" });
                    if (r.ok) {
                        // Анимация удаления
                        msgEl.style.transform = "translateX(30px)";
                        msgEl.style.opacity = "0";
                        setTimeout(() => {
                            msgEl.remove();

                            // Удаляем разделитель даты, если больше нет сообщений за эту дату
                            if (dateLabel) {
                                const remainingMessages = UI.messagesList.querySelectorAll(
                                    `.message[data-date-label="${CSS.escape(dateLabel)}"]`
                                );
                                if (remainingMessages.length === 0) {
                                    // Ищем разделитель с такой же надписью
                                    const divider = Array.from(UI.messagesList.querySelectorAll('.date-divider'))
                                        .find(d => d.textContent === dateLabel);
                                    if (divider) {
                                        divider.remove();
                                    }
                                }
                            }

                            DarkToast.success("Сообщение удалено");
                        }, 300);
                    } else {
                        throw new Error();
                    }
                } catch (e) {
                    DarkToast.error("Ошибка удаления");
                }
                UI.deleteModal.classList.remove("visible");
            };

            UI.deleteModal.querySelector(".delete-cancel-btn").onclick = () => UI.deleteModal.classList.remove("visible");
        },

        resetInput() {
            STATE.editingMsgId = null;
            STATE.editingAttachments = null;
            STATE.editingAttachmentsToDelete = null;
            this.setEditorHtml("");
            UI.cancelEditBtn.classList.add("hidden");
            this.clearFileSelection();
            UI.sendBtn.classList.remove("hidden");
        },

        async markRead(ids) {
            if (ids.length === 0 || !STATE.currentChatId) return;

            try {
                await apiFetch(`${App.API_BASE}/${STATE.currentChatId}/messages/read`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message_ids: ids })
                });

                // Синхронизируем UI в списке чатов
                if (App.List) {
                    App.List.updateChatReadStatus(STATE.currentChatId);
                }

                // Мгновенно обновляем счётчик непрочитанных чатов в навигации (без перезагрузки).
                if (typeof window.refreshUnreadChatsCount === "function") {
                    window.refreshUnreadChatsCount();
                }
            } catch (e) {
                console.warn("Failed to mark messages as read:", e);
            }
        },

        // ПОЛЛИНГ НОВЫХ СООБЩЕНИЙ (каждые 7 секунд)
        startPolling() {
            if (STATE.msgPollTimer) clearInterval(STATE.msgPollTimer);

            STATE.msgPollTimer = setInterval(async () => {
                if (!STATE.currentChatId || document.hidden) return;

                try {
                    let url = `${App.API_BASE}/${STATE.currentChatId}/messages/updates`;
                    if (STATE.lastMessageId != null) {
                        url += `?after_id=${encodeURIComponent(STATE.lastMessageId)}`;
                    } else if (STATE.lastMessageISO) {
                        url += `?since=${encodeURIComponent(STATE.lastMessageISO)}`;
                    }

                    const r = await fetch(url);
                    if (!r.ok) return;

                    const newMsgsBatch = await r.json();
                    if (!Array.isArray(newMsgsBatch) || newMsgsBatch.length === 0) return;

                    const newest = newMsgsBatch[0];
                    STATE.lastMessageId = newest.msg_id;
                    STATE.lastMessageISO = Utils.getISOTimestamp(newest.date_iso || newest.date);

                    const unreadIds = [];
                    const fragment = document.createDocumentFragment();

                    // Разворачиваем, чтобы вставить в конец по порядку [Oldest ... Newest]
                    [...newMsgsBatch].reverse().forEach(m => {
                        // Защита от дубликатов в DOM
                        if (!document.querySelector(`.message[data-msg-id="${m.msg_id}"]`)) {
                            fragment.appendChild(this.createMessageEl(m));
                            // Собираем ID непрочитанных входящих сообщений
                            if (Number(m.answer) === 0 && !m.has_read) {
                                unreadIds.push(m.msg_id);
                            }
                        }
                    });

                    if (fragment.children.length > 0) {
                        const newUrls = Array.from(fragment.querySelectorAll('.message-image-thumb, .message-image')).filter(img => img.style.display !== 'none').map(img => img.src);
                        UI.messagesList.appendChild(fragment);
                        if (newUrls.length && this.gallery) this.gallery.prependToGallery(newUrls);
                        if (STATE.windowedMode) STATE.maxLoadedId = Math.max(STATE.maxLoadedId || 0, STATE.lastMessageId);

                        const container = UI.messagesContainer;
                        const isBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 400;
                        if (isBottom) {
                            Utils.scrollToBottom(200);
                            if (UI.scrollToBottomBtn) UI.scrollToBottomBtn.classList.remove("has-new-below");
                            setTimeout(() => this.updateScrollToBottomBtn(), 250);
                        } else {
                            if (UI.scrollToBottomBtn) UI.scrollToBottomBtn.classList.add("has-new-below");
                            this.updateScrollToBottomBtn();
                        }

                        if (App.List) App.List.moveChatToTop(STATE.currentChatId);
                    }

                    if (unreadIds.length > 0) {
                        unreadIds.forEach(msgId => {
                            const msgEl = UI.messagesList.querySelector(`.message[data-msg-id="${msgId}"]`);
                            if (msgEl) msgEl.classList.remove("unread");
                        });
                        this.markRead(unreadIds);
                    }
                } catch (e) {
                    console.warn("Polling error:", e);
                }
            }, 7000);
        },
    };

    document.addEventListener("DOMContentLoaded", () => App.Messages.init());
})(window.ChatApp);