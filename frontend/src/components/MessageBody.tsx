import { messageContentToHtml, sanitizeMessageHtml } from "@/utils/messageHtml";

type MessageBodyProps = {
  text: string | null | undefined;
  className?: string;
};

function htmlModifierClass(base: string): string {
  if (base === "tk-intro__text") return "tk-msg-text--html";
  return `${base}--html`;
}

export default function MessageBody({ text, className = "tk-msg-text" }: MessageBodyProps) {
  const html = messageContentToHtml(text);
  if (!html) return null;

  return (
    <div
      className={`${className} ${htmlModifierClass(className)}`}
      dangerouslySetInnerHTML={{ __html: sanitizeMessageHtml(html) }}
    />
  );
}
