import { messageLooksLikeHtml, normalizeMessageContent, sanitizeMessageHtml } from "@/utils/messageHtml";

type MessageBodyProps = {
  text: string;
  className?: string;
};

function htmlModifierClass(base: string): string {
  if (base === "tk-intro__text") return "tk-msg-text--html";
  return `${base}--html`;
}

export default function MessageBody({ text, className = "tk-msg-text" }: MessageBodyProps) {
  const normalized = normalizeMessageContent(text);
  if (!normalized) return null;

  if (messageLooksLikeHtml(normalized)) {
    return (
      <div
        className={`${className} ${htmlModifierClass(className)}`}
        dangerouslySetInnerHTML={{ __html: sanitizeMessageHtml(normalized) }}
      />
    );
  }

  return <div className={className}>{normalized}</div>;
}
