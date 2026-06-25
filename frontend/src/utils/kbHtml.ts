import DOMPurify from "dompurify";

let _hooksReady = false;

function escapeHtmlAttr(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

/** Парсит два строковых аргумента showDiagResult('…', '…'). */
function parseTwoSingleQuotedArgs(args: string): [string, string] | null {
  let pos = 0;
  const readOne = (): string | null => {
    while (pos < args.length && /[\s,]/.test(args[pos])) pos += 1;
    if (pos >= args.length || args[pos] !== "'") return null;
    pos += 1;
    let out = "";
    while (pos < args.length) {
      const ch = args[pos];
      if (ch === "'") {
        if (args[pos + 1] === "'") {
          out += "'";
          pos += 2;
          continue;
        }
        pos += 1;
        return out;
      }
      out += ch;
      pos += 1;
    }
    return null;
  };

  const first = readOne();
  const second = readOne();
  if (first === null || second === null) return null;
  return [first, second];
}

/** onclick showDiagResult → data-diag-status / data-diag-action (onclick DOMPurify удаляет). */
function preprocessDiagButtons(html: string): string {
  return html.replace(
    /<button\b([^>]*?\bclass="[^"]*\bdiag-btn\b[^"]*"[^>]*?)\bonclick="showDiagResult\(([\s\S]*?)\)"([^>]*)>/gi,
    (match, before, args, after) => {
      const parsed = parseTwoSingleQuotedArgs(args.trim());
      if (!parsed) return match;
      const [status, action] = parsed;
      return `<button type="button" ${before.trim()} data-diag-status="${escapeHtmlAttr(status)}" data-diag-action="${escapeHtmlAttr(action)}" ${after.trim()}>`;
    },
  );
}

function ensurePurifyHooks(): void {
  if (_hooksReady) return;
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A") {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer");
    }
    if (node.tagName === "INPUT") {
      const className = node.getAttribute("class") || "";
      if (className.includes("ui-form-input")) {
        node.setAttribute("readonly", "");
        node.setAttribute("tabindex", "-1");
      }
      node.removeAttribute("name");
    }
  });
  _hooksReady = true;
}

/** Безопасный HTML тела статьи базы знаний. */
export function sanitizeKbHtml(html: string): string {
  ensurePurifyHooks();
  const prepared = preprocessDiagButtons(html);
  return DOMPurify.sanitize(prepared, {
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
      "img",
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
      "autocomplete",
      "data-diag-status",
      "data-diag-action",
      "src",
      "alt",
      "width",
      "height",
      "loading",
    ],
    ALLOW_DATA_ATTR: false,
  });
}
