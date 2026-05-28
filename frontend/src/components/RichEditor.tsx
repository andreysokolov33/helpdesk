import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { TextStyle, Color, BackgroundColor } from "@tiptap/extension-text-style";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";

// ── Palettes ──────────────────────────────────────────────────────────────────

const TEXT_COLORS = [
  { value: "", label: "Обычный цвет" },
  { value: "#ef4444", label: "Красный" },
  { value: "#f97316", label: "Оранжевый" },
  { value: "#eab308", label: "Жёлтый" },
  { value: "#16a34a", label: "Зелёный" },
  { value: "#2563eb", label: "Синий" },
  { value: "#9333ea", label: "Фиолетовый" },
  { value: "#ec4899", label: "Розовый" },
];

const BG_COLORS = [
  { value: "", label: "Без выделения" },
  { value: "#fef08a", label: "Жёлтое" },
  { value: "#bbf7d0", label: "Зелёное" },
  { value: "#bfdbfe", label: "Синее" },
  { value: "#fce7f3", label: "Розовое" },
  { value: "#ede9fe", label: "Лавандовое" },
  { value: "#fed7aa", label: "Оранжевое" },
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
  rightActions?: React.ReactNode;
};

type ToolPanel = "color" | "heading" | null;

// ── Component ─────────────────────────────────────────────────────────────────

const RichEditor = forwardRef<RichEditorHandle, Props>(function RichEditor(
  { placeholder = "", disabled = false, onSubmit, onEscape, onChange, rightActions },
  ref,
) {
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
      TextStyle,
      Color,
      BackgroundColor,
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
  const activeColor = (editor.getAttributes("textStyle").color as string | undefined) ?? "";
  const activeBg = (editor.getAttributes("textStyle").backgroundColor as string | undefined) ?? "";
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
            className={`tk-rte__btn${(activeColor || activeBg) ? " tk-rte__btn--on" : ""}${panel === "color" ? " tk-rte__btn--on" : ""}`}
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
                borderBottomColor: activeColor || "currentColor",
                background: activeBg || "transparent",
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
                    key={c.value || "_t0"}
                    type="button"
                    className={`tk-rte__swatch${c.value === activeColor ? " tk-rte__swatch--on" : ""}`}
                    title={c.label}
                    style={c.value ? { background: c.value } : undefined}
                    data-reset={!c.value ? "1" : undefined}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      c.value
                        ? editor.chain().focus().setColor(c.value).run()
                        : editor.chain().focus().unsetColor().run();
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
                    key={c.value || "_b0"}
                    type="button"
                    className={`tk-rte__swatch tk-rte__swatch--bg${c.value === activeBg ? " tk-rte__swatch--on" : ""}`}
                    title={c.label}
                    style={c.value ? { background: c.value } : undefined}
                    data-reset={!c.value ? "1" : undefined}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      c.value
                        ? editor.chain().focus().setBackgroundColor(c.value).run()
                        : editor.chain().focus().unsetBackgroundColor().run();
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
