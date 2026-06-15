import type { TrackerTicketListItem } from "@/api/tracker";

export type HomeRatingItem = {
  ticket_id: number;
  rating: number;
  rating_comment: string | null;
  rated_at: string | null;
  subscriber_name: string;
};

export type HomeDashboardResponse = {
  ratings: HomeRatingItem[];
};

export type HomeDashboardDigest = {
  changed: boolean;
  digest: string;
  count: number;
};

export type HomeDashboardDigest = {
  changed: boolean;
  digest: string;
  count: number;
};

export type HomeTicketsResponse = {
  total_open: number;
  needs_reply_count: number;
  needs_reply: TrackerTicketListItem[];
  open: TrackerTicketListItem[];
};

export type HomeTicketsDigest = {
  changed: boolean;
  digest: string;
  total_open: number;
  needs_reply_count: number;
};

export async function fetchHomeTickets(): Promise<HomeTicketsResponse> {
  const res = await fetch("/api/v1/helpdesk/home/tickets", {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<HomeTicketsResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as HomeTicketsResponse;
}

export async function fetchHomeTicketsDigest(params?: {
  digest?: string;
}): Promise<HomeTicketsDigest> {
  const sp = new URLSearchParams();
  if (params?.digest) sp.set("digest", params.digest);
  const qs = sp.toString();
  const res = await fetch(`/api/v1/helpdesk/home/tickets/digest${qs ? `?${qs}` : ""}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<HomeTicketsDigest>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as HomeTicketsDigest;
}

export async function fetchHomeDashboard(): Promise<HomeDashboardResponse> {
  const res = await fetch("/api/v1/helpdesk/home/dashboard", {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<HomeDashboardResponse>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as HomeDashboardResponse;
}

export async function fetchHomeDashboardDigest(params?: {
  digest?: string;
}): Promise<HomeDashboardDigest> {
  const sp = new URLSearchParams();
  if (params?.digest) sp.set("digest", params.digest);
  const qs = sp.toString();
  const res = await fetch(`/api/v1/helpdesk/home/dashboard/digest${qs ? `?${qs}` : ""}`, {
    method: "GET",
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<HomeDashboardDigest>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as HomeDashboardDigest;
}
