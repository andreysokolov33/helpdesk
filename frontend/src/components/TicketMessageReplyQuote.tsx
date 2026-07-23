import type { TicketMessageReplyPreview } from "@/api/ticket";
import { formatStaffNameShort } from "@/utils/personName";
import { messageContentToInlinePreviewHtml } from "@/utils/messageHtml";

type Props = {
  preview: TicketMessageReplyPreview;
  onJump?: (preview: TicketMessageReplyPreview) => void;
};

export default function TicketMessageReplyQuote({ preview, onJump }: Props) {
  if (preview.is_deleted) {
    return (
      <div className="tk-reply-quote tk-reply-quote--deleted" role="note">
        Сообщение удалено
      </div>
    );
  }

  const raw = preview.author_name?.trim() || "Сообщение";
  const label =
    raw === "Сообщение" || raw === "Вы" || raw === "Абонент" || raw === "КЦ" || raw === "Инженер" || raw === "Партнёр"
      ? raw
      : formatStaffNameShort(raw);
  const snippetHtml = messageContentToInlinePreviewHtml(preview.text ?? "");

  return (
    <button
      type="button"
      className="tk-reply-quote"
      onClick={() => onJump?.(preview)}
      title="Перейти к сообщению"
    >
      <span className="tk-reply-quote__author">{label}</span>
      <span
        className="tk-reply-quote__text"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: snippetHtml }}
      />
    </button>
  );
}
