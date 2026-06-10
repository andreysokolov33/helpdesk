export async function loginRequest(login: string, password: string): Promise<Response> {
  return fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ login, password }),
  });
}

export async function logoutRequest(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
}

export type AuthMe = {
  user_id: number;
  role: string | null;
  login?: string | null;
  full_name?: string | null;
};

export async function fetchAuthMe(): Promise<AuthMe> {
  const res = await fetch("/api/auth/me", { method: "GET", credentials: "include" });
  const data = (await res.json().catch(() => ({}))) as { detail?: string } & Partial<AuthMe>;
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  if (data.user_id == null) throw new Error("Некорректный ответ сервера");
  return {
    user_id: data.user_id,
    role: data.role ?? null,
    login: data.login ?? null,
    full_name: data.full_name ?? null,
  };
}
