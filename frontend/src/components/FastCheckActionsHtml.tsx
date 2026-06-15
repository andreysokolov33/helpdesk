import { useEffect, useRef } from "react";
import {
  bindFastCheckCopyHandlers,
  sanitizeFastCheckActionsHtml,
} from "@/utils/fastCheckActionsHtml";

type Props = {
  html: string;
  className?: string;
};

export default function FastCheckActionsHtml({ html, className }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    bindFastCheckCopyHandlers(root);
  }, [html]);

  if (!html.trim()) return null;

  return (
    <div
      ref={rootRef}
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizeFastCheckActionsHtml(html) }}
    />
  );
}
