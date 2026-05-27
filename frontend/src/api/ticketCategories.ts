export type TicketCategoryLeaf = {
  id: number;
  name: string;
  slug: string;
  theme: string;
  complexity: string;
  priority: string;
  priority_label: string;
  support_line: number;
  sla_minutes: number;
  need_user_selection: boolean;
  need_station_selection: boolean;
  object_type: string | null;
};

export type TicketCategoryGroup = {
  id: number;
  name: string;
  slug: string;
  children: TicketCategoryLeaf[];
};

export type TicketCategoriesResponse = {
  catalog_source: string;
  items: TicketCategoryGroup[];
};

async function apiJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export async function fetchTicketCategories(ticketSource?: string | null): Promise<TicketCategoriesResponse> {
  const q = ticketSource ? `?source=${encodeURIComponent(ticketSource)}` : "";
  return apiJson(`/api/v1/helpdesk/tracker/categories${q}`);
}
