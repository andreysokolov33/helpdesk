import { useState } from "react";
import FileBadge, { resolveFileExt, truncateFilename } from "@/components/FileBadge";
import type { TicketMessage } from "@/api/ticket";
import { attachmentImageGridClass, attachmentImageSpanClass } from "@/utils/ticketMessages";

function AttachmentImage({ src, alt }: { src: string; alt: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <span className="tk-att-img__nophoto">
        <span className="tk-att-img__nophoto-icon">🖼</span>
        Нет фото
      </span>
    );
  }
  return <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />;
}

type Props = {
  msg: TicketMessage;
  onOpenImage: (url: string) => void;
};

export default function TicketMessageAttachments({ msg, onOpenImage }: Props) {
  const items = [
    ...(msg.legacy_file_url
      ? [
          {
            id: -1,
            file_path: msg.legacy_file_url,
            original_filename: "Файл",
            is_image: /\.(jpe?g|png|gif|webp|bmp)$/i.test(msg.legacy_file_url),
          },
        ]
      : []),
    ...(msg.attachments || []),
  ];
  if (!items.length) return null;
  const images = items.filter((a) => Boolean(a.is_image));
  const files = items.filter((a) => !a.is_image);
  const n = images.length;
  return (
    <div className="tk-att">
      {images.length ? (
        <div className={attachmentImageGridClass(n)}>
          {images.map((a, i) => {
            const spanClass = attachmentImageSpanClass(i, n);
            return (
            <button
              key={a.id}
              type="button"
              className={spanClass ? `tk-att-img ${spanClass}` : "tk-att-img"}
              onClick={() => onOpenImage(a.file_path)}
              title={a.original_filename || "Открыть изображение"}
            >
              <AttachmentImage src={a.file_path} alt={a.original_filename || "Вложение"} />
            </button>
            );
          })}
        </div>
      ) : null}
      {files.length ? (
        <div className="tk-att-files">
          {files.map((a) => (
            <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-file">
              <FileBadge filename={a.original_filename} ext={resolveFileExt(a.original_filename)} />
              <span className="tk-att-file__name" title={a.original_filename || undefined}>
                {truncateFilename(a.original_filename || "Файл")}
              </span>
            </a>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function collectMessageImageUrls(messages: TicketMessage[]): string[] {
  const out: string[] = [];
  for (const m of messages) {
    if (m.legacy_file_url && /\.(jpe?g|png|gif|webp|bmp)$/i.test(m.legacy_file_url)) {
      out.push(m.legacy_file_url);
    }
    for (const a of m.attachments || []) {
      if (a.is_image && a.file_path) out.push(a.file_path);
    }
  }
  return out.filter((u, i) => out.indexOf(u) === i);
}
