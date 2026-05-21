import { messageLooksLikeHtml, normalizeMessageContent, sanitizeMessageHtml } from "@/utils/messageHtml";

type MessageBodyProps = {
  text: string;
  className?: string;
};

export default function MessageBody({ text, className = "tk-msg-text" }: MessageBodyProps) {
  const normalized = normalizeMessageContent(text);
  if (!normalized) return null;

  if (messageLooksLikeHtml(normalized)) {
    return (
      <div
        className={`${className} tk-msg-text--html`}
        dangerouslySetInnerHTML={{ __html: sanitizeMessageHtml(normalized) }}
      />
    );
  }

  return <div className={className}>{normalized}</div>;
}
