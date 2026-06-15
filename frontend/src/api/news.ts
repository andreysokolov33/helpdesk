export type OperatorNewsBellItem = {
  id: number;
  title: string;
  kind: "general" | "training" | "alert" | string;
  importance: "normal" | "important" | "featured" | string;
  link_path: string | null;
  published_at: string;
};

export type OperatorNewsBellResponse = {
  unread_count: number;
  items: OperatorNewsBellItem[];
};

export type OperatorNewsBellDigest = {
  changed: boolean;
  digest: string;
  unread_count: number;
};

export type OperatorNewsListItem = OperatorNewsBellItem & {
  is_read: boolean;
  read_at: string | null;
};

export type OperatorNewsListResponse = {
  total: number;
  unread_total: number;
  items: OperatorNewsListItem[];
};

export const OPERATOR_NEWS_PAGE_SIZE = 20;

export type OperatorNewsDetail = {
  id: number;
  title: string;
  body_html: string;
  kind: string;
  importance: string;
  link_path: string | null;
  published_at: string;
  is_read: boolean;
};

async function newsJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchOperatorNewsBell(): Promise<OperatorNewsBellResponse> {
  return newsJson<OperatorNewsBellResponse>("/api/v1/helpdesk/news/bell");
}

export async function fetchOperatorNewsHistory(params?: {
  limit?: number;
  offset?: number;
}): Promise<OperatorNewsListResponse> {
  const sp = new URLSearchParams();
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.offset != null) sp.set("offset", String(params.offset));
  const qs = sp.toString();
  return newsJson<OperatorNewsListResponse>(`/api/v1/helpdesk/news${qs ? `?${qs}` : ""}`);
}

export async function fetchOperatorNewsBellDigest(params?: {
  digest?: string;
}): Promise<OperatorNewsBellDigest> {
  const sp = new URLSearchParams();
  if (params?.digest) sp.set("digest", params.digest);
  const qs = sp.toString();
  return newsJson<OperatorNewsBellDigest>(
    `/api/v1/helpdesk/news/bell/digest${qs ? `?${qs}` : ""}`,
  );
}

export async function fetchOperatorNewsDetail(newsId: number): Promise<OperatorNewsDetail> {
  return newsJson<OperatorNewsDetail>(`/api/v1/helpdesk/news/${newsId}`);
}

export async function markOperatorNewsRead(newsId: number): Promise<void> {
  await newsJson<{ ok: boolean }>(`/api/v1/helpdesk/news/${newsId}/read`, { method: "POST" });
}

export function formatNewsRelativeTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return "только что";
  const min = Math.floor(diffMs / 60_000);
  if (min < 1) return "только что";
  if (min < 60) return `${min} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const days = Math.floor(h / 24);
  if (days < 7) return `${days} дн назад`;
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

export function operatorNewsKindLabel(kind: string): string | null {
  switch (kind) {
    case "training":
      return "Обучение";
    case "alert":
      return "Оповещение";
    case "general":
      return null;
    default:
      return null;
  }
}

/** Срочная новость: оповещение или повышенная важность. */
export function isOperatorNewsUrgent(item: Pick<OperatorNewsBellItem, "kind" | "importance">): boolean {
  return (
    item.kind === "alert" ||
    item.importance === "important" ||
    item.importance === "featured"
  );
}
