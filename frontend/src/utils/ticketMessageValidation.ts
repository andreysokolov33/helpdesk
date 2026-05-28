export type TicketMessageValidationReason =
  | "empty"
  | "dots_only"
  | "punctuation_only"
  | "too_brief";

export type TicketMessageValidationResult =
  | { ok: true }
  | { ok: false; reason: TicketMessageValidationReason; message: string };

export const TICKET_MSG_VALIDATION_MESSAGES: Record<TicketMessageValidationReason, string> = {
  empty: "Нельзя отправить пустое сообщение. Добавьте текст, изображение или файл.",
  dots_only: "Нельзя отправить сообщение из одних точек.",
  punctuation_only: "Сообщение должно содержать слова, а не только знаки препинания.",
  too_brief: "Пожалуйста, используйте более развёрнутые ответы — клиенту нужна понятная информация.",
};

const DOTS_ONLY_RE = /^[\s.\u2026…·]+$/u;
const LETTER_RE = /\p{L}/u;
const SINGLE_SHORT_WORD_RE = /^[\p{L}]{1,3}$/u;

/** Явные односложные ответы, которые не стоит отправлять клиенту. */
const BRIEF_RESPONSES = new Set([
  "ok",
  "ок",
  "okay",
  "окей",
  "k",
  "да",
  "нет",
  "ага",
  "угу",
  "ну",
  "хм",
  "hm",
  "mmm",
  "ммм",
  "yes",
  "no",
  "yep",
  "nope",
  "ya",
  "неа",
  "спс",
  "thx",
  "пон",
  "понял",
  "ясно",
  "принял",
  "ладно",
  "норм",
  "norm",
  "clear",
  "done",
  "готово",
  "++",
  "+",
]);

/** HTML редактора → plain text для проверок. */
export function htmlToPlainText(html: string): string {
  const trimmed = html.trim();
  if (!trimmed) return "";
  const el = document.createElement("div");
  el.innerHTML = trimmed;
  return (el.textContent || "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeForBriefCheck(text: string): string {
  return text
    .toLowerCase()
    .replace(/[\s.,!?…:;—–\-'"«»()[\]{}]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isTooBrief(plain: string): boolean {
  const normalized = normalizeForBriefCheck(plain);
  if (!normalized) return false;
  if (BRIEF_RESPONSES.has(normalized)) return true;
  const words = normalized.split(/\s+/).filter(Boolean);
  return words.length === 1 && SINGLE_SHORT_WORD_RE.test(words[0]);
}

export function validateTicketMessage(
  html: string,
  hasAttachments: boolean,
): TicketMessageValidationResult {
  const plain = htmlToPlainText(html);

  if (!plain) {
    if (hasAttachments) return { ok: true };
    return {
      ok: false,
      reason: "empty",
      message: TICKET_MSG_VALIDATION_MESSAGES.empty,
    };
  }

  if (DOTS_ONLY_RE.test(plain)) {
    return {
      ok: false,
      reason: "dots_only",
      message: TICKET_MSG_VALIDATION_MESSAGES.dots_only,
    };
  }

  if (!LETTER_RE.test(plain)) {
    return {
      ok: false,
      reason: "punctuation_only",
      message: TICKET_MSG_VALIDATION_MESSAGES.punctuation_only,
    };
  }

  if (isTooBrief(plain)) {
    return {
      ok: false,
      reason: "too_brief",
      message: TICKET_MSG_VALIDATION_MESSAGES.too_brief,
    };
  }

  return { ok: true };
}
