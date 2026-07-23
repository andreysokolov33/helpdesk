import DOMPurify from "dompurify";
import { marked } from "marked";

marked.setOptions({
  breaks: true,
  gfm: true,
});

const HTML_TAG_RE = /<\/?[a-z][\s\S]*?>/i;
/** Уже отформатированный HTML редактора (не сырой Markdown в тегах). */
const RICH_HTML_RE =
  /<\/?(?:strong|b|em|i|u|s|strike|code|pre|h[1-6]|ul|ol|li|blockquote|table|img|a)\b/i;
/** Признаки Markdown в тексте. */
const MD_HINT_RE =
  /(?:^|\n)\s{0,3}#{1,6}\s+|(?:^|\n)\s{0,3}(?:[-*+]|\d+\.)\s+|\*\*[^*\n]+?\*\*|__[^_\n]+?__|(?<![\w*])\*[^*\n]+?\*(?![\w*])|(?<![\w_])_[^_\n]+?_(?![\w_])|`[^`\n]+`|\[[^\]]+\]\([^)\s]+\)|~~[^~\n]+~~/m;

let _hooksReady = false;

function ensurePurifyHooks(): void {
  if (_hooksReady) return;
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A") {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer");
    }
    if (node.tagName === "IMG") {
      const src = node.getAttribute("src") || "";
      if (src.startsWith("javascript:") || src.startsWith("data:")) {
        node.removeAttribute("src");
      }
    }
  });
  _hooksReady = true;
}

const ENTITY_ESCAPE_RE = /&(?:lt|gt|amp|quot|#\d+|#x[\da-f]+);/i;

function decodeHtmlEntities(text: string): string {
  if (!ENTITY_ESCAPE_RE.test(text)) return text;
  const el = document.createElement("textarea");
  el.innerHTML = text;
  return el.value;
}

/** Нормализует текст сообщения перед рендером (экранированный HTML → разметка). */
export function normalizeMessageContent(text: string | null | undefined): string {
  const trimmed = (text ?? "").trim();
  if (!trimmed) return "";
  const decoded = decodeHtmlEntities(trimmed);
  return HTML_TAG_RE.test(decoded) ? decoded : trimmed;
}

/** Есть ли в строке HTML-разметка. */
export function messageLooksLikeHtml(text: string | null | undefined): boolean {
  return HTML_TAG_RE.test(normalizeMessageContent(text));
}

function looksLikeMarkdown(text: string): boolean {
  return MD_HINT_RE.test(text);
}

/**
 * HTML-оболочка (часто `<p>…</p>` из TipTap) → текст-источник для Markdown.
 * Сохраняет переносы строк по блочным тегам.
 */
function htmlToMarkdownSource(html: string): string {
  let s = html
    .replace(/\r\n?/g, "\n")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(?:p|div|h[1-6]|li|tr)>/gi, "\n")
    .replace(/<\/(?:ul|ol|table|blockquote|pre)>/gi, "\n\n");
  s = s.replace(/<[^>]+>/g, "");
  s = decodeHtmlEntities(s)
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return s;
}

/** Преобразует Markdown в HTML для отображения в чате. */
export function messageMarkdownToHtml(text: string): string {
  const parsed = marked.parse(text, { async: false });
  return typeof parsed === "string" ? parsed : "";
}

/** HTML для тела сообщения: готовый HTML или Markdown → HTML. */
export function messageContentToHtml(text: string): string {
  const normalized = normalizeMessageContent(text);
  if (!normalized) return "";

  if (!messageLooksLikeHtml(normalized)) {
    return messageMarkdownToHtml(normalized);
  }

  // TipTap часто хранит сырой Markdown внутри <p>…</p> без rich-тегов.
  const hasRich = RICH_HTML_RE.test(normalized);
  const mdSource = htmlToMarkdownSource(normalized);
  if (!hasRich && looksLikeMarkdown(mdSource)) {
    return messageMarkdownToHtml(mdSource);
  }

  return normalized;
}

/** Безопасный HTML для тела сообщения в чате. */
export function sanitizeMessageHtml(html: string): string {
  ensurePurifyHooks();
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      "p",
      "br",
      "b",
      "strong",
      "i",
      "em",
      "u",
      "s",
      "a",
      "ul",
      "ol",
      "li",
      "span",
      "div",
      "blockquote",
      "pre",
      "code",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "img",
      "table",
      "thead",
      "tbody",
      "tr",
      "th",
      "td",
    ],
    ALLOWED_ATTR: [
      "href",
      "target",
      "rel",
      "class",
      "style",
      "src",
      "alt",
      "title",
      "colspan",
      "rowspan",
      "data-tc",
      "data-bg",
    ],
    ALLOW_DATA_ATTR: false,
  });
}

const INLINE_PREVIEW_TAGS = ["b", "strong", "i", "em", "u", "s", "code", "a", "span"];

/**
 * Однострочное превью (очередь / цитата): Markdown/HTML → безопасный inline HTML.
 */
export function messageContentToInlinePreviewHtml(
  text: string | null | undefined,
  fallback = "…",
): string {
  const raw = (text ?? "").trim();
  if (!raw) return fallback;
  const html = messageContentToHtml(raw);
  if (!html) return fallback;
  ensurePurifyHooks();
  const flat = html
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<\/(?:p|div|h[1-6]|li)>/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  const clean = DOMPurify.sanitize(flat, {
    ALLOWED_TAGS: INLINE_PREVIEW_TAGS,
    ALLOWED_ATTR: ["href", "target", "rel", "class", "data-tc", "data-bg"],
  }).trim();
  return clean || fallback;
}
