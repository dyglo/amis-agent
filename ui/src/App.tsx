import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, StatsResponse } from "./api";

type OutboxItem = {
  id: number;
  status: string;
  to_email: string | null;
  subject: string | null;
  created_at: string;
  approved_by_human: boolean;
  approved_by: string | null;
  company_name: string;
};

type OutboxDetail = {
  id: number;
  status: string;
  to_email: string | null;
  subject: string | null;
  subject_variants: string[] | null;
  body_text: string | null;
  followup_text: string | null;
  personalization_fact: string | null;
  personalization_source_url: string | null;
  llm_model: string | null;
  llm_confidence: number | null;
  llm_rationale: string | null;
  created_at: string;
  approved_by_human: boolean;
  approved_by: string | null;
  lead: { id: number; contact_email: string | null; contact_name: string | null; contact_role: string | null; status: string };
  company: { id: number; name: string; website_url: string | null; industry: string | null; region: string | null };
};

type CompanyItem = {
  id: number;
  name: string;
  industry: string | null;
  region: string | null;
  website_url: string | null;
  source: string | null;
  created_at: string;
};

type LeadItem = {
  id: number;
  company_name: string;
  contact_email: string | null;
  contact_status: string;
  status: string;
  created_at: string;
};

type SettingsView = {
  enable_sending: boolean;
  s3_enabled: boolean;
  gmail_sender: string;
  demo_mode: boolean;
};

const tabs = ["Dashboard", "Outbox", "Companies/Leads", "Settings"] as const;

export default function App() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Dashboard");
  const [token, setToken] = useState<string | null>(localStorage.getItem("amis_admin_token"));
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [outboxItems, setOutboxItems] = useState<OutboxItem[]>([]);
  const [outboxStatus, setOutboxStatus] = useState("ready_for_review");
  const [outboxDetail, setOutboxDetail] = useState<OutboxDetail | null>(null);
  const [companies, setCompanies] = useState<CompanyItem[]>([]);
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [search, setSearch] = useState("");
  const [settings, setSettings] = useState<SettingsView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<string>("");

  const tokenLabel = useMemo(() => (token ? "Admin token loaded" : "Missing admin token"), [token]);

  useEffect(() => {
    if (!token) return;
    apiGet<StatsResponse>("/api/stats", token)
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    apiGet<{ items: OutboxItem[] }>(`/api/outbox?status=${outboxStatus}&limit=50`, token)
      .then((res) => setOutboxItems(res.items))
      .catch((err) => setError(err.message));
  }, [token, outboxStatus]);

  useEffect(() => {
    if (!token) return;
    apiGet<{ items: CompanyItem[] }>(`/api/companies?search=${encodeURIComponent(search)}`, token)
      .then((res) => setCompanies(res.items))
      .catch((err) => setError(err.message));
    apiGet<{ items: LeadItem[] }>(`/api/leads?search=${encodeURIComponent(search)}`, token)
      .then((res) => setLeads(res.items))
      .catch((err) => setError(err.message));
  }, [token, search]);

  useEffect(() => {
    if (!token) return;
    apiGet<SettingsView>("/api/settings", token)
      .then(setSettings)
      .catch((err) => setError(err.message));
  }, [token]);

  const refreshOutbox = () => {
    if (!token) return;
    apiGet<{ items: OutboxItem[] }>(`/api/outbox?status=${outboxStatus}&limit=50`, token)
      .then((res) => setOutboxItems(res.items))
      .catch((err) => setError(err.message));
  };

  const handleTokenSave = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) {
      localStorage.removeItem("amis_admin_token");
      setToken(null);
      return;
    }
    localStorage.setItem("amis_admin_token", trimmed);
    setToken(trimmed);
  };

  const sendDisabled = settings ? !settings.enable_sending : true;
  const demoMode = settings?.demo_mode ?? false;

  return (
    <div className="min-h-screen bg-gradient-to-br from-sand via-white to-slate-200">
      <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6">
        <div className="space-y-2">
          <span className="pill">AMIS Agent Console</span>
          <h1 className="text-3xl font-semibold text-ink">Operate the outreach engine.</h1>
          <p className="text-sm text-dusk">Production controls for qualification, enrichment, and review.</p>
        </div>
        <div className="card w-full max-w-md space-y-3">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Admin token</div>
          <input
            type="password"
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="Paste X-ADMIN-TOKEN"
            defaultValue={token ?? ""}
            onBlur={(e) => handleTokenSave(e.target.value)}
          />
          <div className="text-xs text-slate-500">{tokenLabel}</div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16">
        {demoMode && (
          <div className="mb-6 rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm font-semibold text-indigo-700">
            DEMO MODE ENABLED
          </div>
        )}
        <nav className="mb-8 flex flex-wrap gap-3">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={activeTab === tab ? "btn bg-slate-900 text-white" : "btn-muted"}
            >
              {tab}
            </button>
          ))}
        </nav>

        {error && <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

        {activeTab === "Dashboard" && (
          <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <div className="card space-y-6">
              <h2 className="text-xl font-semibold">System pulse</h2>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-white p-4 shadow">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Companies</div>
                  <div className="text-3xl font-semibold">{stats?.companies ?? "--"}</div>
                </div>
                <div className="rounded-2xl bg-white p-4 shadow">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Leads (ready)</div>
                  <div className="text-3xl font-semibold">{stats?.leads_by_status?.ready_for_review ?? 0}</div>
                </div>
                <div className="rounded-2xl bg-white p-4 shadow">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Outbox ready</div>
                  <div className="text-3xl font-semibold">{stats?.outbox_by_status?.ready_for_review ?? 0}</div>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-slate-600">Last runs</h3>
                  <ul className="mt-3 space-y-2 text-sm text-slate-600">
                    {stats?.last_runs &&
                      Object.entries(stats.last_runs).map(([key, value]) => (
                        <li key={key} className="flex items-center justify-between">
                          <span className="font-medium">{key}</span>
                          <span>{value ? new Date(value).toLocaleString() : "--"}</span>
                        </li>
                      ))}
                  </ul>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-slate-600">Recent activity</h3>
                  <ul className="mt-3 space-y-2 text-sm text-slate-600">
                    {stats?.recent_activity?.map((entry, idx) => (
                      <li key={idx} className="flex items-center justify-between">
                        <span>{entry.action}</span>
                        <span>{new Date(entry.created_at).toLocaleTimeString()}</span>
                      </li>
                    )) ?? <li>--</li>}
                  </ul>
                </div>
              </div>
            </div>
            <div className="card space-y-4">
              <h2 className="text-xl font-semibold">Quick actions</h2>
              <button
                type="button"
                className="btn"
                onClick={() => {
                  setError(null);
                  setPipelineStatus(`triggered at ${new Date().toLocaleTimeString()}`);
                  apiPost("/api/run/pipeline", token)
                    .then(() => setPipelineStatus(`enqueued at ${new Date().toLocaleTimeString()}`))
                    .catch((err) => setError(err.message));
                }}
              >
                Run pipeline once
              </button>
              <button
                type="button"
                className="btn-muted"
                onClick={() => {
                  setError(null);
                  apiPost("/api/demo/seed", token)
                    .then(() => setPipelineStatus(`demo data seeded at ${new Date().toLocaleTimeString()}`))
                    .catch((err) => setError(err.message));
                }}
              >
                Seed demo data
              </button>
              {pipelineStatus && (
                <div className="text-xs text-slate-500">Pipeline: {pipelineStatus}</div>
              )}
              <button className="btn-muted" onClick={() => window.location.reload()}>
                Refresh data
              </button>
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
                ENABLE_SENDING is {sendDisabled ? "OFF" : "ON"}.
              </div>
            </div>
          </section>
        )}

        {activeTab === "Outbox" && (
          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="card">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Outbox review</h2>
                  <p className="text-sm text-slate-600">Select a draft to inspect and approve.</p>
                </div>
                <select
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={outboxStatus}
                  onChange={(e) => setOutboxStatus(e.target.value)}
                >
                  <option value="ready_for_review">ready_for_review</option>
                  <option value="approved">approved</option>
                  <option value="sent">sent</option>
                </select>
              </div>
              <div className="mt-6 max-h-[460px] overflow-auto rounded-2xl border border-slate-200 bg-white">
                <table className="w-full text-left text-sm">
                  <thead className="sticky top-0 bg-slate-50 text-xs uppercase tracking-[0.2em] text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Company</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {outboxItems.map((item) => (
                      <tr
                        key={item.id}
                        className="cursor-pointer border-t border-slate-100 hover:bg-slate-50"
                        onClick={() =>
                          apiGet<OutboxDetail>(`/api/outbox/${item.id}`, token)
                            .then(setOutboxDetail)
                            .catch((err) => setError(err.message))
                        }
                      >
                        <td className="px-4 py-3 font-medium">{item.company_name}</td>
                        <td className="px-4 py-3">{item.subject}</td>
                        <td className="px-4 py-3 text-xs uppercase">{item.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button className="btn-muted" onClick={refreshOutbox}>
                  Refresh
                </button>
              </div>
            </div>
            <div className="card space-y-4">
              <h2 className="text-xl font-semibold">Draft detail</h2>
              {outboxDetail ? (
                <div className="space-y-4 text-sm text-slate-700">
                  <div className="space-y-1">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Subject</div>
                    <div className="font-semibold">{outboxDetail.subject}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Body</div>
                    <pre className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs">
                      {outboxDetail.body_text}
                    </pre>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Personalization</div>
                    <div>{outboxDetail.personalization_fact ?? "--"}</div>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <button
                      className="btn"
                      onClick={() =>
                        apiPost(`/api/outbox/${outboxDetail.id}/approve`, token)
                          .then(() => refreshOutbox())
                          .catch((err) => setError(err.message))
                      }
                    >
                      Approve
                    </button>
                    <button
                      className="btn-muted"
                      onClick={() =>
                        apiPost(`/api/outbox/${outboxDetail.id}/regenerate`, token)
                          .then(() => refreshOutbox())
                          .catch((err) => setError(err.message))
                      }
                    >
                      Regenerate
                    </button>
                    <button
                      className={sendDisabled ? "btn-muted" : "btn"}
                      disabled={sendDisabled}
                      onClick={() =>
                        apiPost(`/api/outbox/${outboxDetail.id}/send`, token)
                          .then(() => refreshOutbox())
                          .catch((err) => setError(err.message))
                      }
                    >
                      Send
                    </button>
                  </div>
                  {sendDisabled && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
                      Sending is disabled. Set ENABLE_SENDING=true in the server env to enable.
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-slate-500">Select an outbox row to view details.</div>
              )}
            </div>
          </section>
        )}

        {activeTab === "Companies/Leads" && (
          <section className="grid gap-6 lg:grid-cols-2">
            <div className="card space-y-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">Companies</h2>
                <input
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  placeholder="Search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <ul className="space-y-3 text-sm text-slate-700">
                {companies.map((company) => (
                  <li key={company.id} className="rounded-xl border border-slate-200 bg-white p-3">
                    <div className="font-semibold">{company.name}</div>
                    <div className="text-xs text-slate-500">
                      {company.industry ?? "--"} · {company.region ?? "--"}
                    </div>
                    <div className="text-xs text-slate-500">{company.website_url ?? "--"}</div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="card space-y-4">
              <h2 className="text-xl font-semibold">Leads</h2>
              <ul className="space-y-3 text-sm text-slate-700">
                {leads.map((lead) => (
                  <li key={lead.id} className="rounded-xl border border-slate-200 bg-white p-3">
                    <div className="font-semibold">{lead.company_name}</div>
                    <div className="text-xs text-slate-500">{lead.contact_email ?? "--"}</div>
                    <div className="text-xs uppercase text-slate-400">
                      {lead.status} · {lead.contact_status}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {activeTab === "Settings" && (
          <section className="card space-y-4">
            <h2 className="text-xl font-semibold">Settings (read-only)</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">ENABLE_SENDING</div>
                <div className="text-lg font-semibold">{settings?.enable_sending ? "true" : "false"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">S3_ENABLED</div>
                <div className="text-lg font-semibold">{settings?.s3_enabled ? "true" : "false"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Sender</div>
                <div className="text-lg font-semibold">{settings?.gmail_sender ?? "--"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">DEMO_MODE</div>
                <div className="text-lg font-semibold">{settings?.demo_mode ? "true" : "false"}</div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
