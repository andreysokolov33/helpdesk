import type { TicketMessageReplyPreview } from "@/api/ticket";

type Props = {
  preview: TicketMessageReplyPreview;
  onJump?: (id: number) => void;
};

export default function TicketMessageReplyQuote({ preview, onJump }: Props) {
  if (preview.is_deleted) {
    return (
      <div className="tk-reply-quote tk-reply-quote--deleted" role="note">
        Сообщение удалено
      </div>
    );
  }

  const label = preview.author_name?.trim() || "Сообщение";
  const snippet = preview.text?.trim() || "…";

  return (
    <button
      type="button"
      className="tk-reply-quote"
      onClick={() => onJump?.(preview.id)}
      title="Перейти к сообщению"
    >
      <span className="tk-reply-quote__author">{label}</span>
      <span className="tk-reply-quote__text">{snippet}</span>
    </button>
  );
}
