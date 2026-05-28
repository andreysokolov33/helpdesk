import DOMPurify from "dompurify";

const HTML_TAG_RE = /<\/?[a-z][\s\S]*?>/i;

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
export function normalizeMessageContent(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "";
  const decoded = decodeHtmlEntities(trimmed);
  return HTML_TAG_RE.test(decoded) ? decoded : trimmed;
}

/** Есть ли в строке HTML-разметка. */
export function messageLooksLikeHtml(text: string): boolean {
  return HTML_TAG_RE.test(normalizeMessageContent(text));
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
    ALLOWED_ATTR: ["href", "target", "rel", "class", "style", "src", "alt", "title", "colspan", "rowspan", "data-tc", "data-bg"],
    ALLOW_DATA_ATTR: false,
  });
}
