export type SubscriberSearchHit = {
  id: number;
  login: string;
  name: string;
  email: string | null;
  phone: string | null;
  id_doc: string | null;
  is_juridical: number;
  station_id?: number | null;
  hotspot_id?: number | null;
};

export type DeskSearchResponse = {
  subscribers: SubscriberSearchHit[];
  kb: { id: number; title: string; excerpt?: string | null }[];
};

export async function fetchDeskSearch(q: string, limit = 15): Promise<DeskSearchResponse> {
  const sp = new URLSearchParams({ q: q.trim(), limit: String(limit) });
  const res = await fetch(`/api/v1/helpdesk/search?${sp.toString()}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<DeskSearchResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return {
    subscribers: data.subscribers ?? [],
    kb: data.kb ?? [],
  };
}
