export type OperatorManageItem = {
  id: number;
  login: string;
  full_name: string | null;
  email: string | null;
  is_active: boolean;
  is_online: boolean;
  level: number | null;
  open_tickets_count: number;
};

export type OperatorManageStats = {
  active_count: number;
  online_count: number;
};

export type OperatorManageList = {
  admins: OperatorManageItem[];
  operators: OperatorManageItem[];
  stats: OperatorManageStats;
};

async function parseError(res: Response): Promise<string> {
  const data = (await res.json().catch(() => ({}))) as { detail?: string | { msg?: string }[] };
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  return `HTTP ${res.status}`;
}

export async function fetchOperatorsManage(): Promise<OperatorManageList> {
  const res = await fetch("/api/v1/helpdesk/operators/manage", {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<OperatorManageList>;
}

export async function fetchSuggestedOperatorLogin(): Promise<string> {
  const res = await fetch("/api/v1/helpdesk/operators/manage/suggested-login", {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = (await res.json()) as { login: string };
  return data.login;
}

export async function createOperator(payload: {
  login: string;
  password: string;
  full_name: string;
  email?: string | null;
}): Promise<OperatorManageItem> {
  const res = await fetch("/api/v1/helpdesk/operators/manage", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<OperatorManageItem>;
}

export async function updateOperator(
  operatorId: number,
  payload: { full_name?: string; is_active?: boolean },
): Promise<OperatorManageItem> {
  const res = await fetch(`/api/v1/helpdesk/operators/manage/${operatorId}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<OperatorManageItem>;
}

export async function resetOperatorPassword(operatorId: number, password: string): Promise<void> {
  const res = await fetch(`/api/v1/helpdesk/operators/manage/${operatorId}/password`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function sendOperatorPresence(): Promise<void> {
  await fetch("/api/v1/helpdesk/operators/me/presence", {
    method: "POST",
    credentials: "include",
  }).catch(() => {});
}
