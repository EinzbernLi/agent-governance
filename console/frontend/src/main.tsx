/// <reference types="vite/client" />

import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type RepositorySummary = {
  repository: string;
  branch: string;
  commit_sha: string;
  version: string;
};

type LeadState = {
  status: string;
  generation: number | null;
  claim_comment_id: number | null;
  activation_comment_id: number | null;
  conflict_comment_ids: number[];
  lead_issue: number;
};

type IssueSummary = {
  number: number;
  title: string;
  url: string;
  updated_at: string | null;
  labels: string[];
};

type PullRequestSummary = {
  number: number;
  title: string;
  url: string;
  draft: boolean;
  state: string;
  head_ref: string;
  head_sha: string;
  base_ref: string;
  updated_at: string | null;
};

type DashboardSummary = {
  authority_mode: "derived_read_only" | string;
  repository: RepositorySummary;
  lead: LeadState;
  issues: IssueSummary[];
  pull_requests: PullRequestSummary[];
};

const configuredBase = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
const API_BASE = configuredBase.replace(/\/$/, "");

function shortSha(sha: string): string {
  return sha.length > 12 ? sha.slice(0, 12) : sha;
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

async function loadDashboard(signal: AbortSignal): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE}/api/v1/dashboard`, { signal });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }
  return (await response.json()) as DashboardSummary;
}

function LeadCard({ lead }: { lead: LeadState }) {
  const conflict = lead.status === "conflict";
  return (
    <section className="card lead-card">
      <div className="card-heading">
        <span>Active Lead</span>
        <span className={`status status-${lead.status}`}>{lead.status}</span>
      </div>
      <div className="metric">{lead.generation === null ? "—" : `G${lead.generation}`}</div>
      <dl className="details">
        <div><dt>Lead issue</dt><dd>#{lead.lead_issue}</dd></div>
        <div><dt>Claim</dt><dd>{lead.claim_comment_id ?? "—"}</dd></div>
        <div><dt>Activation</dt><dd>{lead.activation_comment_id ?? "—"}</dd></div>
      </dl>
      {conflict && (
        <p className="warning">
          Duplicate latest-generation claims detected: {lead.conflict_comment_ids.join(", ") || "unknown IDs"}.
          The console will not choose a winner.
        </p>
      )}
    </section>
  );
}

function App() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    loadDashboard(controller.signal)
      .then((value) => {
        setData(value);
        setError(null);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : String(reason));
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Agent Governance</p>
          <h1>Governance Console</h1>
          <p className="subtitle">A derived operator view over canonical GitHub governance facts.</p>
        </div>
        <div className="readonly">READ ONLY · NON-AUTHORITATIVE</div>
      </header>

      {error && (
        <section className="error-panel">
          <strong>Governance state unavailable.</strong>
          <p>{error}</p>
          <p>No ACTIVE state has been inferred.</p>
        </section>
      )}

      {!data && !error && <div className="loading">Loading durable GitHub facts…</div>}

      {data && (
        <>
          <section className="grid summary-grid">
            <section className="card">
              <div className="card-heading"><span>Repository</span><span>v{data.repository.version}</span></div>
              <div className="metric repo-name">{data.repository.repository}</div>
              <dl className="details">
                <div><dt>Branch</dt><dd>{data.repository.branch}</dd></div>
                <div><dt>Exact SHA</dt><dd><code>{shortSha(data.repository.commit_sha)}</code></dd></div>
                <div><dt>Authority mode</dt><dd>{data.authority_mode}</dd></div>
              </dl>
            </section>
            <LeadCard lead={data.lead} />
            <section className="card compact-card">
              <div className="card-heading"><span>Open work</span></div>
              <div className="split-metrics">
                <div><span className="metric">{data.issues.length}</span><small>Issues</small></div>
                <div><span className="metric">{data.pull_requests.length}</span><small>PRs</small></div>
              </div>
            </section>
          </section>

          <section className="grid work-grid">
            <section className="panel">
              <div className="panel-heading"><h2>Open Issues</h2><span>{data.issues.length}</span></div>
              <div className="rows">
                {data.issues.length === 0 && <p className="empty">No open issues.</p>}
                {data.issues.map((issue) => (
                  <a className="row" href={issue.url} target="_blank" rel="noreferrer" key={issue.number}>
                    <div>
                      <strong>#{issue.number} {issue.title}</strong>
                      <div className="labels">
                        {issue.labels.map((label) => <span key={label}>{label}</span>)}
                      </div>
                    </div>
                    <time>{formatDate(issue.updated_at)}</time>
                  </a>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading"><h2>Pull Requests</h2><span>{data.pull_requests.length}</span></div>
              <div className="rows">
                {data.pull_requests.length === 0 && <p className="empty">No open pull requests.</p>}
                {data.pull_requests.map((pr) => (
                  <a className="row" href={pr.url} target="_blank" rel="noreferrer" key={pr.number}>
                    <div>
                      <strong>#{pr.number} {pr.title}</strong>
                      <div className="meta-line">
                        {pr.draft ? "draft · " : ""}{pr.head_ref} → {pr.base_ref} · <code>{shortSha(pr.head_sha)}</code>
                      </div>
                    </div>
                    <time>{formatDate(pr.updated_at)}</time>
                  </a>
                ))}
              </div>
            </section>
          </section>

          <footer>
            GitHub Issues, PRs, repository files and canonical Lead comments remain the durable authority.
          </footer>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
