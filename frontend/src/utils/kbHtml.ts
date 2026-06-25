import DOMPurify from "dompurify";

let _hooksReady = false;

function ensurePurifyHooks(): void {
  if (_hooksReady) return;
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A") {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer");
    }
    if (node.tagName === "INPUT") {
      node.setAttribute("readonly", "");
      node.setAttribute("tabindex", "-1");
      node.removeAttribute("name");
    }
  });
  _hooksReady = true;
}

/** Безопасный HTML тела статьи базы знаний. */
export function sanitizeKbHtml(html: string): string {
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
      "a",
      "ul",
      "ol",
      "li",
      "span",
      "div",
      "h1",
      "h2",
      "h3",
      "h4",
      "table",
      "thead",
      "tbody",
      "tr",
      "th",
      "td",
      "button",
      "input",
    ],
    ALLOWED_ATTR: [
      "href",
      "target",
      "rel",
      "class",
      "id",
      "style",
      "colspan",
      "rowspan",
      "type",
      "placeholder",
      "value",
      "readonly",
    ],
    ALLOW_DATA_ATTR: false,
  });
}
