export type StatsResponse = {
  companies: number;
  leads_by_status: Record<string, number>;
  outbox_by_status: Record<string, number>;
  last_runs: Record<string, string | null>;
  recent_activity: { action: string; source: string | null; created_at: string }[];
};

const baseHeaders = (token: string | null) => ({
  "Content-Type": "application/json",
  ...(token ? { "X-ADMIN-TOKEN": token } : {}),
});

export async function apiGet<T>(path: string, token: string | null): Promise<T> {
  const res = await fetch(path, { headers: baseHeaders(token) });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, token: string | null): Promise<T> {
  const res = await fetch(path, { method: "POST", headers: baseHeaders(token) });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as T;
}
