export type ProfilePersonal = {
  user_id: number;
  name: string;
  login: string;
  email: string | null;
  phone: string | null;
  id_doc: string | null;
  is_juridical: number;
  entity_label: string;
  user_status: number | null;
  status_label: string;
  station_name: string | null;
  auth_page: string | null;
};

export type ProfileOnline = {
  is_online: boolean;
  last_session_end: string | null;
  last_session_end_label: string | null;
};

export type ProfileTariff = {
  state: "active" | "inactive" | "frozen" | "planned_freeze";
  tariff_name: string;
  real_type: string | null;
  is_active: boolean;
  rate_up: string;
  rate_down: string;
  speed_unlimited: boolean;
  remain_traffic_mb: number;
  full_packet_mb: number;
  jur_main_packet_mb: number | null;
  jur_dop_packet_mb: number | null;
  overrun_mb: number | null;
  traffic_renew_count: number | null;
  msk_reset: string | null;
  local_reset: string | null;
  valid_date_label: string | null;
  disconnect_at_label: string | null;
  planned_freeze_at: string | null;
  frozen_at: string | null;
  unfreeze_at: string | null;
  frozen_remaining_label: string | null;
  freeze_reason: string | null;
  can_freeze: boolean;
  can_unfreeze: boolean;
  can_cancel_planned_freeze: boolean;
  can_disconnect_sessions: boolean;
};

export type ProfileTicket = {
  id: number;
  title: string;
  category: string | null;
  category_theme: string | null;
  date_of_create: string;
  date_of_close: string | null;
  assigned_to_role: string | null;
  support_line: number;
  support_line_label: string;
  status: string;
  status_label: string;
};

export type UserProfileResponse = {
  personal: ProfilePersonal;
  online: ProfileOnline;
  open_sessions_count: number;
  balance: number;
  tariff: ProfileTariff | null;
  netflow_note: string | null;
  netflow_tariff: string | null;
  health_check: { items: string[] };
  tickets: ProfileTicketListResponse;
};

export type ProfileTicketListResponse = {
  total: number;
  page: number;
  per_page: number;
  items: ProfileTicket[];
};

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<T>;
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
  }
  return data as T;
}

export function fetchUserProfile(
  userId: number,
  ticketsPage = 1,
  ticketsPerPage = 10,
): Promise<UserProfileResponse> {
  const q = new URLSearchParams({
    tickets_page: String(ticketsPage),
    tickets_per_page: String(ticketsPerPage),
  });
  return api(`/api/v1/helpdesk/users/${userId}/profile?${q}`);
}

export function fetchUserProfileTickets(
  userId: number,
  page = 1,
  perPage = 10,
): Promise<ProfileTicketListResponse> {
  const q = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  return api(`/api/v1/helpdesk/users/${userId}/profile/tickets?${q}`);
}

export function postUnarchive(userId: number) {
  return api<{ message: string }>(`/api/v1/helpdesk/users/${userId}/unarchive`, { method: "POST" });
}

export function postUnfreeze(userId: number) {
  return api<{ message: string }>(`/api/v1/helpdesk/users/${userId}/unfreeze`, { method: "POST" });
}

export function deleteFreezePlan(userId: number) {
  return api<{ message: string }>(`/api/v1/helpdesk/users/${userId}/freeze-plan`, { method: "DELETE" });
}

export function postFreeze(userId: number, body: { date_freeze?: string | null; date_unfreeze?: string | null }) {
  return api<{ message: string }>(`/api/v1/helpdesk/users/${userId}/freeze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function postDisconnect(userId: number) {
  return api<{ message: string }>(`/api/v1/helpdesk/users/${userId}/disconnect-sessions`, { method: "POST" });
}

export type PasswordResetState = {
  has_ppp_sessions: boolean;
  active_code: string | null;
  expires_at: string | null;
  can_generate: boolean;
  code_id: number | null;
};

export type PasswordResetGenerateResult = {
  code: string;
  expires_at: string;
  code_id: number;
  message: string;
};

export type PasswordResetPoll = {
  code_used: boolean;
  code_expired: boolean;
  active_code: string | null;
  expires_at: string | null;
  code_id: number | null;
};

export function fetchPasswordResetState(userId: number): Promise<PasswordResetState> {
  return api(`/api/v1/helpdesk/users/${userId}/password-reset`);
}

export function fetchPasswordResetPoll(userId: number, codeId: number): Promise<PasswordResetPoll> {
  return api(`/api/v1/helpdesk/users/${userId}/password-reset/poll?code_id=${codeId}`);
}

export function generatePasswordResetCode(userId: number): Promise<PasswordResetGenerateResult> {
  return api(`/api/v1/helpdesk/users/${userId}/password-reset/generate`, { method: "POST" });
}
