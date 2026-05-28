import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import { Mark, mergeAttributes } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";

// ── Custom mark extensions ─────────────────────────────────────────────────────

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    textColor: {
      setTextColor(color: string): ReturnType;
      unsetTextColor(): ReturnType;
    };
    bgColor: {
      setBgColor(color: string): ReturnType;
      unsetBgColor(): ReturnType;
    };
  }
}

const TextColorMark = Mark.create({
  name: "textColor",
  addAttributes() {
    return {
      color: {
        default: null,
        parseHTML: (el) => (el as HTMLElement).getAttribute("data-tc"),
        renderHTML: (attrs) => (attrs.color ? { "data-tc": attrs.color } : {}),
      },
    };
  },
  parseHTML() {
    return [{ tag: "span[data-tc]" }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes), 0];
  },
  addCommands() {
    return {
      setTextColor:
        (color: string) =>
        ({ commands }) =>
          commands.setMark(this.name, { color }),
      unsetTextColor:
        () =>
        ({ commands }) =>
          commands.unsetMark(this.name),
    };
  },
});

const BgColorMark = Mark.create({
  name: "bgColor",
  addAttributes() {
    return {
      color: {
        default: null,
        parseHTML: (el) => (el as HTMLElement).getAttribute("data-bg"),
        renderHTML: (attrs) => (attrs.color ? { "data-bg": attrs.color } : {}),
      },
    };
  },
  parseHTML() {
    return [{ tag: "span[data-bg]" }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes), 0];
  },
  addCommands() {
    return {
      setBgColor:
        (color: string) =>
        ({ commands }) =>
          commands.setMark(this.name, { color }),
      unsetBgColor:
        () =>
        ({ commands }) =>
          commands.unsetMark(this.name),
    };
  },
});

// ── Palettes (keys → CSS variables) ──────────────────────────────────────────

const TEXT_COLORS = [
  { key: "",         label: "Обычный" },
  { key: "red",      label: "Красный" },
  { key: "orange",   label: "Оранжевый" },
  { key: "yellow",   label: "Жёлтый" },
  { key: "green",    label: "Зелёный" },
  { key: "blue",     label: "Синий" },
  { key: "purple",   label: "Фиолетовый" },
  { key: "pink",     label: "Розовый" },
];

const BG_COLORS = [
  { key: "",         label: "Без фона" },
  { key: "yellow",   label: "Жёлтый" },
  { key: "green",    label: "Зелёный" },
  { key: "blue",     label: "Синий" },
  { key: "pink",     label: "Розовый" },
  { key: "lavender", label: "Лавандовый" },
  { key: "orange",   label: "Оранжевый" },
];

const HEADING_LEVELS = [1, 2, 3] as const;

// ── Types ─────────────────────────────────────────────────────────────────────

export type RichEditorHandle = {
  readonly isEmpty: boolean;
  getHTML(): string;
  setContent(html: string): void;
  focus(): void;
  clear(): void;
};

type Props = {
  placeholder?: string;
  disabled?: boolean;
  onSubmit?(): void;
  onEscape?(): void;
  onChange?(isEmpty: boolean): void;
  onPasteFiles?(files: File[]): void;
  rightActions?: React.ReactNode;
};

type ToolPanel = "color" | null;

// ── Component ─────────────────────────────────────────────────────────────────

const RichEditor = forwardRef<RichEditorHandle, Props>(function RichEditor(
  { placeholder = "", disabled = false, onSubmit, onEscape, onChange, onPasteFiles, rightActions },
  ref,
) {
  const onPasteFilesRef = useRef(onPasteFiles);
  useEffect(() => { onPasteFilesRef.current = onPasteFiles; }, [onPasteFiles]);
  const [panel, setPanel] = useState<ToolPanel>(null);
  const [linkOpen, setLinkOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkText, setLinkText] = useState("");
  const [hasSelection, setHasSelection] = useState(false);
  const linkUrlRef = useRef<HTMLInputElement>(null);
  const linkTextRef = useRef<HTMLInputElement>(null);

  const editor = useEditor({
    extensions: [
      StarterKit,
      TextColorMark,
      BgColorMark,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: { rel: "noopener noreferrer", target: "_blank" },
      }),
      Placeholder.configure({ placeholder }),
    ],
    editable: !disabled,
    editorProps: {
      attributes: { class: "tk-rte__area", spellcheck: "true" },
      handleKeyDown(_, event) {
        if (event.ctrlKey && event.key === "Enter") {
          event.preventDefault();
          onSubmit?.();
          return true;
        }
        if (event.key === "Escape") {
          onEscape?.();
          return true;
        }
        return false;
      },
      handlePaste(_, event) {
        const cb = onPasteFilesRef.current;
        if (!cb) return false;
        const items = Array.from(event.clipboardData?.items ?? []);
        const files = items
          .filter((it) => it.kind === "file" && it.type.startsWith("image/"))
          .map((it) => {
            const f = it.getAsFile();
            if (!f) return null;
            const ext = f.type.split("/")[1]?.replace("jpeg", "jpg") || "png";
            const rand = Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 6);
            return new File([f], `${rand}.${ext}`, { type: f.type });
          })
          .filter((f): f is File => f !== null);
        if (!files.length) return false;
        event.preventDefault();
        cb(files);
        return true;
      },
    },
    onUpdate({ editor: e }) {
      onChange?.(e.isEmpty);
    },
    onSelectionUpdate({ editor: e }) {
      setHasSelection(!e.state.selection.empty);
    },
  });

  useEffect(() => {
    if (!editor) return;
    const ext = editor.extensionManager.extensions.find((e) => e.name === "placeholder");
    if (ext) {
      ext.options.placeholder = placeholder;
      editor.view.dispatch(editor.state.tr.setMeta("placeholder", placeholder));
    }
  }, [editor, placeholder]);

  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!disabled);
  }, [editor, disabled]);

  useImperativeHandle(ref, () => ({
    get isEmpty() {
      return editor?.isEmpty ?? true;
    },
    getHTML() {
      return editor?.getHTML() ?? "";
    },
    setContent(html: string) {
      editor?.commands.setContent(html || "", true);
    },
    focus() {
      requestAnimationFrame(() => editor?.commands.focus("end"));
    },
    clear() {
      editor?.commands.clearContent(true);
    },
  }));

  const applyLink = useCallback(() => {
    if (!editor) return;
    const url = linkUrl.trim();
    if (!url) { setLinkOpen(false); return; }
    const href = /^https?:\/\//i.test(url) ? url : `https://${url}`;
    if (hasSelection) {
      editor.chain().focus().setLink({ href }).run();
    } else {
      const text = linkText.trim() || href;
      editor
        .chain()
        .focus()
        .insertContent({ type: "text", marks: [{ type: "link", attrs: { href } }], text })
        .run();
    }
    setLinkOpen(false);
    setLinkUrl("");
    setLinkText("");
  }, [editor, linkUrl, linkText, hasSelection]);

  const openLink = useCallback(() => {
    if (!editor) return;
    setPanel(null);
    if (linkOpen) { setLinkOpen(false); return; }
    const existingHref = editor.getAttributes("link").href as string | undefined;
    setLinkUrl(existingHref ?? "");
    setLinkText("");
    setLinkOpen(true);
  }, [editor, linkOpen]);

  useEffect(() => {
    if (!linkOpen) return;
    requestAnimationFrame(() => {
      if (!hasSelection && linkTextRef.current) {
        linkTextRef.current.focus();
      } else if (linkUrlRef.current) {
        linkUrlRef.current.focus();
      }
    });
  }, [linkOpen, hasSelection]);

  if (!editor) return null;

  const isBold = editor.isActive("bold");
  const isBullet = editor.isActive("bulletList");
  const isOrdered = editor.isActive("orderedList");
  const isLink = editor.isActive("link");
  const activeColor = (editor.getAttributes("textColor").color as string | undefined) ?? "";
  const activeBg = (editor.getAttributes("bgColor").color as string | undefined) ?? "";
  const activeHeading = HEADING_LEVELS.find((l) => editor.isActive("heading", { level: l }));

  return (
    <div className="tk-rte">
      <EditorContent editor={editor} />

      {/* Link input form */}
      {linkOpen && (
        <div className="tk-rte__link-form">
          {!hasSelection && (
            <input
              ref={linkTextRef}
              className="tk-rte__link-input"
              placeholder="Текст ссылки"
              value={linkText}
              onChange={(e) => setLinkText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") { e.preventDefault(); applyLink(); }
                if (e.key === "Escape") setLinkOpen(false);
              }}
            />
          )}
          <input
            ref={linkUrlRef}
            className="tk-rte__link-input tk-rte__link-input--url"
            placeholder="https://..."
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") { e.preventDefault(); applyLink(); }
              if (e.key === "Escape") setLinkOpen(false);
            }}
          />
          <button type="button" className="tk-rte__link-ok" onClick={applyLink}>ОК</button>
          <button type="button" className="tk-rte__link-cancel" onClick={() => setLinkOpen(false)}>×</button>
        </div>
      )}

      {/* Toolbar */}
      <div className="tk-rte__bar">

        {/* Bold */}
        <button
          type="button"
          className={`tk-rte__btn${isBold ? " tk-rte__btn--on" : ""}`}
          title="Жирный (Ctrl+B)"
          onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleBold().run(); }}
        >
          <strong>Ж</strong>
        </button>

        {/* Color picker button */}
        <div className="tk-rte__popover-wrap">
          <button
            type="button"
            className={`tk-rte__btn${(activeColor || activeBg || panel === "color") ? " tk-rte__btn--on" : ""}`}
            title="Цвет текста и выделение"
            onMouseDown={(e) => {
              e.preventDefault();
              setLinkOpen(false);
              setPanel((p) => (p === "color" ? null : "color"));
            }}
          >
            <span
              className="tk-rte__color-a"
              style={{
                borderBottomColor: activeColor ? `var(--tc-${activeColor})` : "currentColor",
                background: activeBg ? `var(--bg-${activeBg})` : "transparent",
              }}
            >
              A
            </span>
          </button>

          {panel === "color" && (
            <div className="tk-rte__popover tk-rte__popover--color">
              {/* Text color row */}
              <div className="tk-rte__palette-label">Цвет текста</div>
              <div className="tk-rte__palette">
                {TEXT_COLORS.map((c) => (
                  <button
                    key={c.key || "_t0"}
                    type="button"
                    className={`tk-rte__swatch${c.key === activeColor ? " tk-rte__swatch--on" : ""}`}
                    title={c.label}
                    style={c.key ? { background: `var(--tc-${c.key})` } : undefined}
                    data-reset={!c.key ? "1" : undefined}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      c.key
                        ? editor.chain().focus().setTextColor(c.key).run()
                        : editor.chain().focus().unsetTextColor().run();
                      setPanel(null);
                    }}
                  />
                ))}
              </div>

              {/* Background highlight row */}
              <div className="tk-rte__palette-label" style={{ marginTop: 8 }}>Выделение фона</div>
              <div className="tk-rte__palette">
                {BG_COLORS.map((c) => (
                  <button
                    key={c.key || "_b0"}
                    type="button"
                    className={`tk-rte__swatch tk-rte__swatch--bg${c.key === activeBg ? " tk-rte__swatch--on" : ""}`}
                    title={c.label}
                    style={c.key ? { background: `var(--bg-${c.key})` } : undefined}
                    data-reset={!c.key ? "1" : undefined}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      c.key
                        ? editor.chain().focus().setBgColor(c.key).run()
                        : editor.chain().focus().unsetBgColor().run();
                      setPanel(null);
                    }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="tk-rte__sep" />

        {/* Heading buttons */}
        {HEADING_LEVELS.map((level) => (
          <button
            key={level}
            type="button"
            className={`tk-rte__btn tk-rte__btn--h${activeHeading === level ? " tk-rte__btn--on" : ""}`}
            title={`Заголовок H${level}`}
            onMouseDown={(e) => {
              e.preventDefault();
              editor.chain().focus().toggleHeading({ level }).run();
            }}
          >
            H{level}
          </button>
        ))}

        <div className="tk-rte__sep" />

        {/* Link */}
        <button
          type="button"
          className={`tk-rte__btn${isLink || linkOpen ? " tk-rte__btn--on" : ""}`}
          title="Вставить ссылку"
          onMouseDown={(e) => { e.preventDefault(); openLink(); }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
            <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
          </svg>
        </button>

        {/* Bullet list */}
        <button
          type="button"
          className={`tk-rte__btn${isBullet ? " tk-rte__btn--on" : ""}`}
          title="Маркированный список"
          onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleBulletList().run(); }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
            <line x1="9" y1="6" x2="20" y2="6" />
            <line x1="9" y1="12" x2="20" y2="12" />
            <line x1="9" y1="18" x2="20" y2="18" />
            <circle cx="4" cy="6" r="1.5" fill="currentColor" stroke="none" />
            <circle cx="4" cy="12" r="1.5" fill="currentColor" stroke="none" />
            <circle cx="4" cy="18" r="1.5" fill="currentColor" stroke="none" />
          </svg>
        </button>

        {/* Ordered list */}
        <button
          type="button"
          className={`tk-rte__btn${isOrdered ? " tk-rte__btn--on" : ""}`}
          title="Нумерованный список"
          onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleOrderedList().run(); }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
            <line x1="11" y1="6" x2="21" y2="6" />
            <line x1="11" y1="12" x2="21" y2="12" />
            <line x1="11" y1="18" x2="21" y2="18" />
            <text x="1" y="8.5" fontSize="8" fill="currentColor" stroke="none" fontFamily="monospace">1</text>
            <text x="1" y="14.5" fontSize="8" fill="currentColor" stroke="none" fontFamily="monospace">2</text>
            <text x="1" y="20.5" fontSize="8" fill="currentColor" stroke="none" fontFamily="monospace">3</text>
          </svg>
        </button>

        <div className="tk-rte__spacer" />
        {rightActions}
      </div>
    </div>
  );
});

export default RichEditor;
