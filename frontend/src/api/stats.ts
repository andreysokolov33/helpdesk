export type StatsSummary = {
  date_from: string;
  date_to: string;
  new_tickets: number;
  closed_tickets: number;
  avg_first_response_sec: number | null;
  avg_lifetime_sec: number | null;
  avg_rating: number | null;
  is_admin_view: boolean;
  operator_id: number | null;
  operator_name: string | null;
};

export type OperatorStatsRow = {
  operator_id: number;
  operator_name: string;
  new_tickets: number;
  closed_tickets: number;
  avg_first_response_sec: number | null;
  avg_lifetime_sec: number | null;
  avg_rating: number | null;
};

export type StatsRatingItem = {
  ticket_id: number;
  source: string;
  source_label: string;
  rating: number | null;
  rating_comment: string | null;
  rated_at: string | null;
  lifetime_sec: number | null;
  category_label: string | null;
  engineer_involved: boolean;
};

export type SupportOperatorOption = {
  id: number;
  label: string;
};

export type StatsDashboard = {
  summary: StatsSummary;
  operators: OperatorStatsRow[];
  recent_ratings: StatsRatingItem[];
  operator_options: SupportOperatorOption[];
};

export async function fetchStatsDashboard(params: {
  dateFrom?: string;
  dateTo?: string;
  operatorId?: number | null;
}): Promise<StatsDashboard> {
  const q = new URLSearchParams();
  if (params.dateFrom) q.set("date_from", params.dateFrom);
  if (params.dateTo) q.set("date_to", params.dateTo);
  if (params.operatorId != null) q.set("operator_id", String(params.operatorId));

  const res = await fetch(`/api/v1/helpdesk/stats/dashboard?${q.toString()}`, {
    credentials: "include",
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<StatsDashboard>;
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return data as StatsDashboard;
}
