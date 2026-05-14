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
