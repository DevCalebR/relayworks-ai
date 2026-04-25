"use client";

import type { FormEvent, ReactNode } from "react";
import { startTransition, useEffect, useState } from "react";

import {
  API_BASE_URL,
  PROJECT_ID,
  discoverCandidateLeads,
  formatDateTime,
  formatWebsite,
  getAssetPacks,
  getBackendStatus,
  getCandidateLeads,
  getFollowUpQueue,
  getLatestRecord,
  getLaunchPlans,
  getLeads,
  getOutreachRecords,
  getPipelineMetrics,
  importCandidateLead,
  markOutreachSent,
  previewMessage,
  rejectCandidateLead,
  sortNewestFirst,
  type AssetPack,
  type BackendStatusResponse,
  type CandidateLead,
  type CandidateStatus,
  type FollowUpQueueItem,
  type LaunchPlan,
  type Lead,
  type LeadStatus,
  type OutreachRecord,
  type OutreachStatus,
  type PipelineMetrics,
} from "@/lib/api";

const DEFAULT_DISCOVERY_TARGET =
  "Seed to Series B B2B SaaS companies likely to care about win-loss analysis, revenue operations, sales process improvement, and closed-lost learning loops";

const WORKFLOW_STEPS = [
  "Discover Candidates",
  "Import Leads",
  "Review Drafts",
  "Send Manually",
  "Mark Sent",
  "Follow Up",
  "Track Replies",
];

const LEAD_STATUSES: LeadStatus[] = [
  "new",
  "contacted",
  "replied",
  "interested",
  "closed",
];

const OUTREACH_STATUSES: OutreachStatus[] = ["draft", "sent", "replied", "ignored"];

function humanize(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong while loading this section.";
}

function getStatusTone(status: CandidateStatus | LeadStatus | OutreachStatus): string {
  switch (status) {
    case "discovered":
    case "draft":
    case "new":
      return "bg-amber-100 text-amber-900";
    case "imported":
    case "sent":
    case "contacted":
      return "bg-emerald-100 text-emerald-900";
    case "rejected":
    case "ignored":
      return "bg-rose-100 text-rose-900";
    case "replied":
    case "interested":
      return "bg-sky-100 text-sky-900";
    case "closed":
      return "bg-slate-200 text-slate-800";
    default:
      return "bg-stone-200 text-stone-800";
  }
}

function Badge({
  label,
  tone,
}: {
  label: string;
  tone?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold tracking-[0.14em] uppercase ${
        tone ?? "bg-stone-200 text-stone-800"
      }`}
    >
      {label}
    </span>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-2">
        <p className="font-mono text-[11px] tracking-[0.24em] uppercase text-muted">
          {eyebrow}
        </p>
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted">{description}</p>
        </div>
      </div>
      {action}
    </div>
  );
}

function RefreshButton({
  label,
  onClick,
  disabled,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center justify-center rounded-full border border-border bg-white/70 px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
    >
      {disabled ? `Refreshing ${label}...` : `Refresh ${label}`}
    </button>
  );
}

function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <section className={`glass-panel rounded-[28px] p-6 ${className ?? ""}`}>{children}</section>;
}

function InlineNotice({
  tone = "info",
  children,
}: {
  tone?: "info" | "success" | "warning" | "error";
  children: ReactNode;
}) {
  const classes =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : tone === "error"
          ? "border-rose-200 bg-rose-50 text-rose-900"
          : "border-sky-200 bg-sky-50 text-sky-900";

  return <div className={`rounded-2xl border px-4 py-3 text-sm leading-6 ${classes}`}>{children}</div>;
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-border bg-white/55 px-6 py-10 text-center">
      <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-muted">{description}</p>
    </div>
  );
}

function InfoField({
  label,
  value,
  preserveWhitespace,
}: {
  label: string;
  value: string;
  preserveWhitespace?: boolean;
}) {
  return (
    <div className="space-y-1">
      <p className="font-mono text-[11px] tracking-[0.18em] uppercase text-muted">{label}</p>
      <p
        className={`text-sm leading-6 text-foreground ${
          preserveWhitespace ? "whitespace-pre-wrap" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function DataError({ message }: { message: string }) {
  return <InlineNotice tone="error">{message}</InlineNotice>;
}

function useResource<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadInitially() {
      try {
        const next = await load();
        if (!active) {
          return;
        }
        setData(next);
        setError(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setError(toErrorMessage(error));
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadInitially();

    return () => {
      active = false;
    };
  }, [load]);

  async function refresh() {
    setLoading(true);
    try {
      const next = await load();
      setData(next);
      setError(null);
    } catch (error) {
      setError(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return {
    data,
    error,
    loading,
    refresh,
  };
}

function MetricsCard({
  metrics,
  loading,
  error,
  onRefresh,
}: {
  metrics: PipelineMetrics | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Pipeline"
        title="Pipeline metrics"
        description="Counts come directly from the current project snapshot so the operator can see draft, sent, and lead status totals without opening JSON files."
        action={<RefreshButton label="metrics" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!metrics && loading ? <p className="text-sm text-muted">Loading pipeline metrics...</p> : null}
      {metrics ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {LEAD_STATUSES.map((status) => (
            <StatTile
              key={status}
              label={`Leads · ${humanize(status)}`}
              value={metrics.lead_counts[status]}
            />
          ))}
          <StatTile label="Leads · Total" value={metrics.lead_counts.total} accent />
          {OUTREACH_STATUSES.map((status) => (
            <StatTile
              key={status}
              label={`Outreach · ${humanize(status)}`}
              value={metrics.outreach_counts[status]}
            />
          ))}
          <StatTile label="Outreach · Total" value={metrics.outreach_counts.total} accent />
        </div>
      ) : null}
    </Card>
  );
}

function StatTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-3xl border px-4 py-4 ${
        accent ? "border-emerald-200 bg-emerald-50/70" : "border-border bg-white/65"
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
    </div>
  );
}

function StatusCard({
  status,
  loading,
  error,
}: {
  status: BackendStatusResponse | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <Card className="space-y-4">
      <SectionHeading
        eyebrow="Backend"
        title="Local API status"
        description="This panel calls the FastAPI root endpoint and health endpoint from the browser."
      />
      {error ? <DataError message={error} /> : null}
      {!status && loading ? <p className="text-sm text-muted">Checking backend status...</p> : null}
      {status ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge label={status.online ? "Online" : "Offline"} tone={status.online ? "bg-emerald-100 text-emerald-900" : "bg-rose-100 text-rose-900"} />
            <p className="font-mono text-xs text-muted">{API_BASE_URL}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <InfoField label="GET /" value={status.root.message} />
            <InfoField label="GET /health" value={`status: ${status.health.status}`} />
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function ProjectCard() {
  return (
    <Card className="space-y-4">
      <SectionHeading
        eyebrow="Project"
        title="Active project"
        description="This dashboard is pinned to the current working project so the operator always knows which record set they are touching."
      />
      <div className="space-y-3">
        <Badge label="Current working project" tone="bg-stone-900 text-stone-50" />
        <div className="rounded-3xl border border-border bg-white/65 p-5">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Project ID</p>
          <p className="mt-3 break-all text-lg font-semibold text-foreground">{PROJECT_ID}</p>
          <p className="mt-3 text-sm leading-6 text-muted">
            Use this project as the single place to discover candidates, import leads,
            review drafts, mark manual sends, and inspect follow-ups.
          </p>
        </div>
      </div>
    </Card>
  );
}

function CandidateLeadCard({
  candidate,
  busy,
  onImport,
  onReject,
}: {
  candidate: CandidateLead;
  busy: boolean;
  onImport: (candidateLeadId: string) => void;
  onReject: (candidateLeadId: string) => void;
}) {
  const canReview = candidate.status === "discovered";

  return (
    <article className="rounded-[26px] border border-amber-200 bg-amber-50/75 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge label="Unverified candidate lead" tone="bg-amber-200 text-amber-950" />
            <Badge label={humanize(candidate.status)} tone={getStatusTone(candidate.status)} />
            <Badge label={`Confidence ${candidate.confidence_score}/10`} tone="bg-white text-stone-900" />
          </div>
          <div>
            <h3 className="text-xl font-semibold tracking-tight text-foreground">
              {candidate.company_name}
            </h3>
            <p className="mt-1 text-sm text-muted">
              {candidate.contact_name?.trim() || "No verified contact yet"}
              {" · "}
              {candidate.contact_title?.trim() || "Title still being researched"}
            </p>
          </div>
        </div>
        {canReview ? (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => onImport(candidate.id)}
              className="rounded-full bg-stone-900 px-4 py-2 text-sm font-semibold text-stone-50 transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? "Working..." : "Import"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => onReject(candidate.id)}
              className="rounded-full border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-900 transition hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Reject
            </button>
          </div>
        ) : null}
      </div>
      <p className="mt-4 text-sm leading-6 text-amber-950">
        Candidate discovery suggests possible leads. It does not verify private emails or
        guarantee contact data.
      </p>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <InfoField label="Email" value={candidate.contact_email?.trim() || "No verified email yet"} />
        <InfoField label="Industry" value={candidate.industry?.trim() || "Industry not listed"} />
        <InfoField label="Website" value={formatWebsite(candidate.website)} />
        <InfoField label="Lead source" value={candidate.lead_source?.trim() || "No lead source listed"} />
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <InfoField label="Fit reason" value={candidate.fit_reason} />
        <InfoField label="Created" value={formatDateTime(candidate.created_at)} />
      </div>
    </article>
  );
}

function LeadsTable({
  leads,
  loading,
  error,
  onRefresh,
}: {
  leads: Lead[] | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Leads"
        title="Imported leads"
        description="These are the leads already in the working pipeline. Once candidates are imported, they appear here and move through the manual outreach workflow."
        action={<RefreshButton label="leads" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!leads && loading ? <p className="text-sm text-muted">Loading leads...</p> : null}
      {leads && leads.length === 0 ? (
        <EmptyState
          title="No leads yet"
          description="Imported leads will appear here after you accept candidate leads."
        />
      ) : null}
      {leads && leads.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-3">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.18em] text-muted">
                <th className="px-3">Company</th>
                <th className="px-3">Contact</th>
                <th className="px-3">Email</th>
                <th className="px-3">Status</th>
                <th className="px-3">Industry</th>
                <th className="px-3">Website</th>
                <th className="px-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {sortNewestFirst(leads).map((lead) => (
                <tr key={lead.id} className="rounded-3xl bg-white/65 text-sm text-foreground">
                  <td className="rounded-l-3xl px-3 py-4 font-semibold">{lead.company_name}</td>
                  <td className="px-3 py-4">{lead.contact_name || "No verified contact yet"}</td>
                  <td className="px-3 py-4">{lead.contact_email.trim() || "No email yet"}</td>
                  <td className="px-3 py-4">
                    <Badge label={humanize(lead.status)} tone={getStatusTone(lead.status)} />
                  </td>
                  <td className="px-3 py-4">{lead.industry || "Unknown"}</td>
                  <td className="px-3 py-4">{formatWebsite(lead.website)}</td>
                  <td className="rounded-r-3xl px-3 py-4">{formatDateTime(lead.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  );
}

function OutreachBoard({
  outreach,
  loading,
  error,
  busyOutreachId,
  onRefresh,
  onMarkSent,
}: {
  outreach: OutreachRecord[] | null;
  loading: boolean;
  error: string | null;
  busyOutreachId: string | null;
  onRefresh: () => void;
  onMarkSent: (outreachId: string) => void;
}) {
  const sorted = outreach ? sortNewestFirst(outreach) : [];

  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Outreach"
        title="Drafts and sent outreach"
        description="Draft records are shown here for human review. The frontend never sends email; it only helps the operator inspect messages and mark them as sent after manual delivery."
        action={<RefreshButton label="outreach" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!outreach && loading ? <p className="text-sm text-muted">Loading outreach records...</p> : null}
      {outreach && outreach.length === 0 ? (
        <EmptyState
          title="No outreach records yet"
          description="Drafts and sent outreach will appear here when the backend generates them."
        />
      ) : null}
      {outreach && outreach.length > 0 ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {OUTREACH_STATUSES.map((status) => {
            const items = sorted.filter((record) => record.status === status);

            return (
              <section key={status} className="rounded-[26px] border border-border bg-white/55 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-foreground">{humanize(status)}</h3>
                    <Badge label={`${items.length} records`} tone={getStatusTone(status)} />
                  </div>
                </div>
                <div className="mt-4 space-y-4">
                  {items.length === 0 ? (
                    <p className="text-sm text-muted">No {status} outreach records right now.</p>
                  ) : (
                    items.map((record) => (
                      <article key={record.id} className="rounded-3xl border border-border bg-card-strong p-4">
                        <div className="flex flex-col gap-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge label={humanize(record.status)} tone={getStatusTone(record.status)} />
                            <Badge label={record.channel} tone="bg-stone-200 text-stone-900" />
                          </div>
                          <div className="grid gap-3 md:grid-cols-2">
                            <InfoField label="Lead ID" value={record.lead_id} />
                            <InfoField label="Asset pack ID" value={record.asset_pack_id} />
                          </div>
                          <InfoField label="Created" value={formatDateTime(record.created_at)} />
                          <InfoField
                            label="Message preview"
                            value={previewMessage(record.message)}
                            preserveWhitespace
                          />
                          <details className="rounded-2xl border border-border bg-white/75 p-4">
                            <summary className="cursor-pointer text-sm font-semibold text-foreground">
                              Read full message
                            </summary>
                            <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-foreground">
                              {record.message}
                            </p>
                          </details>
                          {record.status === "draft" ? (
                            <div className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4">
                              <p className="text-sm font-semibold text-amber-950">
                                Only click after you manually sent this message.
                              </p>
                              <button
                                type="button"
                                disabled={busyOutreachId === record.id}
                                onClick={() => onMarkSent(record.id)}
                                className="rounded-full bg-amber-900 px-4 py-2 text-sm font-semibold text-amber-50 transition hover:bg-amber-800 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                {busyOutreachId === record.id ? "Marking..." : "Mark as Sent"}
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </article>
                    ))
                  )}
                </div>
              </section>
            );
          })}
        </div>
      ) : null}
    </Card>
  );
}

function FollowUpSection({
  followUps,
  loading,
  error,
  onRefresh,
}: {
  followUps: FollowUpQueueItem[] | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Follow-ups"
        title="Follow-up queue"
        description="This queue surfaces leads whose most recent outreach was sent and may need another touchpoint."
        action={<RefreshButton label="follow-ups" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!followUps && loading ? <p className="text-sm text-muted">Loading follow-up queue...</p> : null}
      {followUps && followUps.length === 0 ? (
        <EmptyState title="No follow-ups due right now." description="Once a lead needs a follow-up, it will appear here with the last outreach context." />
      ) : null}
      {followUps && followUps.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {followUps.map((item) => (
            <article key={item.last_outreach_id} className="rounded-[26px] border border-border bg-white/65 p-5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge label="Follow-up due" tone="bg-sky-100 text-sky-900" />
                <Badge label={item.channel} tone="bg-stone-200 text-stone-900" />
              </div>
              <h3 className="mt-4 text-xl font-semibold text-foreground">{item.company_name}</h3>
              <p className="mt-1 text-sm text-muted">{item.contact_name}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <InfoField label="Lead ID" value={item.lead_id} />
                <InfoField label="Last outreach ID" value={item.last_outreach_id} />
              </div>
              <InfoField label="Message preview" value={previewMessage(item.message)} preserveWhitespace />
            </article>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

function AssetPackCard({
  assetPack,
  loading,
  error,
}: {
  assetPack: AssetPack | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Assets"
        title="Latest asset pack"
        description="This is the latest messaging package the backend generated for the project."
      />
      {error ? <DataError message={error} /> : null}
      {!assetPack && loading ? <p className="text-sm text-muted">Loading asset pack...</p> : null}
      {!assetPack && !loading && !error ? (
        <EmptyState
          title="No asset pack found yet."
          description="Generate an asset pack in the backend and it will appear here."
        />
      ) : null}
      {assetPack ? (
        <div className="space-y-5">
          <InfoField label="Headline" value={assetPack.headline} />
          <InfoField label="One sentence pitch" value={assetPack.one_sentence_pitch} />
          <InfoField label="Pilot offer" value={assetPack.pilot_offer} preserveWhitespace />
          <InfoField label="Cold outreach email subject" value={assetPack.cold_outreach_email_subject} />
          <InfoField
            label="Cold outreach email body"
            value={assetPack.cold_outreach_email_body}
            preserveWhitespace
          />
          <InfoField label="LinkedIn DM" value={assetPack.linkedin_dm} preserveWhitespace />
        </div>
      ) : null}
    </Card>
  );
}

function LaunchPlanCard({
  launchPlan,
  loading,
  error,
}: {
  launchPlan: LaunchPlan | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Launch"
        title="Latest launch plan"
        description="This section shows the current offer and go-to-market guidance the backend has already generated."
      />
      {error ? <DataError message={error} /> : null}
      {!launchPlan && loading ? <p className="text-sm text-muted">Loading launch plan...</p> : null}
      {!launchPlan && !loading && !error ? (
        <EmptyState
          title="No launch plan found yet."
          description="Generate a launch plan in the backend and it will appear here."
        />
      ) : null}
      {launchPlan ? (
        <div className="space-y-5">
          <InfoField label="Headline" value={launchPlan.headline} />
          <InfoField label="Ideal customer profile" value={launchPlan.ideal_customer_profile} />
          <InfoField label="Offer summary" value={launchPlan.offer_summary} preserveWhitespace />
          <InfoField label="Pricing hypothesis" value={launchPlan.pricing_hypothesis} />
          <InfoField label="Sales motion" value={launchPlan.sales_motion} preserveWhitespace />
          <InfoField
            label="Launch recommendation"
            value={launchPlan.launch_recommendation}
            preserveWhitespace
          />
        </div>
      ) : null}
    </Card>
  );
}

export function OperatorDashboard() {
  const backendStatus = useResource(getBackendStatus);
  const metrics = useResource(getPipelineMetrics);
  const candidates = useResource(getCandidateLeads);
  const leads = useResource(getLeads);
  const outreach = useResource(getOutreachRecords);
  const followUps = useResource(getFollowUpQueue);
  const assetPacks = useResource(getAssetPacks);
  const launchPlans = useResource(getLaunchPlans);

  const [candidateNotice, setCandidateNotice] = useState<string | null>(null);
  const [outreachNotice, setOutreachNotice] = useState<string | null>(null);
  const [candidateActionError, setCandidateActionError] = useState<string | null>(null);
  const [outreachActionError, setOutreachActionError] = useState<string | null>(null);
  const [busyCandidateId, setBusyCandidateId] = useState<string | null>(null);
  const [busyOutreachId, setBusyOutreachId] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [target, setTarget] = useState(DEFAULT_DISCOVERY_TARGET);
  const [count, setCount] = useState(5);

  const latestAssetPack = assetPacks.data ? getLatestRecord(assetPacks.data) : null;
  const latestLaunchPlan = launchPlans.data ? getLatestRecord(launchPlans.data) : null;

  async function handleDiscoverCandidates(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDiscovering(true);
    setCandidateActionError(null);
    setCandidateNotice(null);

    try {
      const discovered = await discoverCandidateLeads({
        target,
        count,
      });
      setCandidateNotice(`Discovery completed. ${discovered.length} candidate lead${discovered.length === 1 ? "" : "s"} returned.`);
      startTransition(() => {
        void candidates.refresh();
      });
    } catch (error) {
      setCandidateActionError(toErrorMessage(error));
    } finally {
      setDiscovering(false);
    }
  }

  async function handleImportCandidate(candidateLeadId: string) {
    setBusyCandidateId(candidateLeadId);
    setCandidateActionError(null);
    setCandidateNotice(null);

    try {
      await importCandidateLead(candidateLeadId);
      setCandidateNotice("Candidate imported into leads.");
      startTransition(() => {
        void Promise.all([candidates.refresh(), leads.refresh(), metrics.refresh()]);
      });
    } catch (error) {
      setCandidateActionError(toErrorMessage(error));
    } finally {
      setBusyCandidateId(null);
    }
  }

  async function handleRejectCandidate(candidateLeadId: string) {
    setBusyCandidateId(candidateLeadId);
    setCandidateActionError(null);
    setCandidateNotice(null);

    try {
      await rejectCandidateLead(candidateLeadId);
      setCandidateNotice("Candidate rejected.");
      startTransition(() => {
        void candidates.refresh();
      });
    } catch (error) {
      setCandidateActionError(toErrorMessage(error));
    } finally {
      setBusyCandidateId(null);
    }
  }

  async function handleMarkSent(outreachId: string) {
    setBusyOutreachId(outreachId);
    setOutreachActionError(null);
    setOutreachNotice(null);

    try {
      await markOutreachSent(outreachId);
      setOutreachNotice("Draft marked as sent and lead status refreshed.");
      startTransition(() => {
        void Promise.all([
          outreach.refresh(),
          leads.refresh(),
          metrics.refresh(),
          followUps.refresh(),
        ]);
      });
    } catch (error) {
      setOutreachActionError(toErrorMessage(error));
    } finally {
      setBusyOutreachId(null);
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-6">
        <Card className="overflow-hidden p-0">
          <div className="border-b border-white/50 bg-[linear-gradient(135deg,rgba(31,106,82,0.92),rgba(16,42,35,0.9)_58%,rgba(154,95,17,0.76))] px-6 py-8 text-stone-50 sm:px-8">
            <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
              <div className="max-w-4xl space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge label="RelayWorks Operator Dashboard" tone="bg-white/16 text-white" />
                  <Badge label="Local-first" tone="bg-black/18 text-white" />
                </div>
                <div className="space-y-3">
                  <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
                    Operate the RelayWorks AI backend without curl.
                  </h1>
                  <p className="max-w-3xl text-base leading-7 text-stone-100/92 sm:text-lg">
                    RelayWorks AI helps you find an opportunity, create an offer,
                    discover candidate leads, import leads, generate outreach drafts,
                    manually send them, and track follow-ups.
                  </p>
                </div>
              </div>
              <div className="rounded-[28px] border border-white/14 bg-black/14 px-5 py-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-stone-200">
                  Backend URL
                </p>
                <p className="mt-2 text-sm font-semibold text-white">{API_BASE_URL}</p>
                <p className="mt-2 text-sm text-stone-200">
                  Beginner-friendly control panel for the current project.
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white/35 px-6 py-5 sm:px-8">
            <div className="flex gap-3 overflow-x-auto pb-1">
              {WORKFLOW_STEPS.map((step, index) => (
                <div
                  key={step}
                  className="flex min-w-max items-center gap-3 rounded-full border border-border bg-white/70 px-4 py-3"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-stone-50">
                    {index + 1}
                  </span>
                  <span className="text-sm font-semibold text-foreground">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <section className="section-grid grid gap-6 xl:grid-cols-[1fr_1fr_1.4fr]">
          <StatusCard
            status={backendStatus.data}
            loading={backendStatus.loading}
            error={backendStatus.error}
          />
          <ProjectCard />
          <MetricsCard
            metrics={metrics.data}
            loading={metrics.loading}
            error={metrics.error}
            onRefresh={metrics.refresh}
          />
        </section>

        <Card className="space-y-6">
          <SectionHeading
            eyebrow="Candidates"
            title="Candidate leads"
            description="These records are discovery suggestions only. Keep the unverified label visible so operators do not confuse candidate data with confirmed contact data."
            action={<RefreshButton label="candidate leads" onClick={candidates.refresh} disabled={candidates.loading} />}
          />
          {candidateNotice ? <InlineNotice tone="success">{candidateNotice}</InlineNotice> : null}
          {candidateActionError ? <InlineNotice tone="error">{candidateActionError}</InlineNotice> : null}
          {candidates.error ? <DataError message={candidates.error} /> : null}
          <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
            <form onSubmit={handleDiscoverCandidates} className="rounded-[28px] border border-border bg-white/60 p-5">
              <div className="space-y-4">
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
                    Candidate discovery
                  </p>
                  <h3 className="mt-2 text-xl font-semibold text-foreground">
                    Request new candidate leads
                  </h3>
                </div>
                <InlineNotice tone="warning">
                  Candidate discovery suggests possible leads. It does not verify private emails
                  or guarantee contact data.
                </InlineNotice>
                <label className="block space-y-2">
                  <span className="text-sm font-semibold text-foreground">Target</span>
                  <textarea
                    value={target}
                    onChange={(event) => setTarget(event.target.value)}
                    rows={7}
                    className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none ring-0 transition focus:border-emerald-500"
                  />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-semibold text-foreground">Count</span>
                  <input
                    type="number"
                    min={1}
                    max={25}
                    value={count}
                    onChange={(event) => setCount(Number(event.target.value))}
                    className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none ring-0 transition focus:border-emerald-500"
                  />
                </label>
                <button
                  type="submit"
                  disabled={discovering}
                  className="w-full rounded-full bg-emerald-900 px-4 py-3 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {discovering ? "Discovering..." : "Discover Candidates"}
                </button>
              </div>
            </form>

            <div className="space-y-4">
              {!candidates.data && candidates.loading ? (
                <p className="text-sm text-muted">Loading candidate leads...</p>
              ) : null}
              {candidates.data && candidates.data.length === 0 ? (
                <EmptyState
                  title="No candidate leads yet"
                  description="Run candidate discovery from the form on the left to populate this section."
                />
              ) : null}
              {candidates.data && candidates.data.length > 0
                ? sortNewestFirst(candidates.data).map((candidate) => (
                    <CandidateLeadCard
                      key={candidate.id}
                      candidate={candidate}
                      busy={busyCandidateId === candidate.id}
                      onImport={handleImportCandidate}
                      onReject={handleRejectCandidate}
                    />
                  ))
                : null}
            </div>
          </div>
        </Card>

        <LeadsTable
          leads={leads.data}
          loading={leads.loading}
          error={leads.error}
          onRefresh={leads.refresh}
        />

        <section className="space-y-4">
          {outreachNotice ? <InlineNotice tone="success">{outreachNotice}</InlineNotice> : null}
          {outreachActionError ? <InlineNotice tone="error">{outreachActionError}</InlineNotice> : null}
          <OutreachBoard
            outreach={outreach.data}
            loading={outreach.loading}
            error={outreach.error}
            busyOutreachId={busyOutreachId}
            onRefresh={outreach.refresh}
            onMarkSent={handleMarkSent}
          />
        </section>

        <FollowUpSection
          followUps={followUps.data}
          loading={followUps.loading}
          error={followUps.error}
          onRefresh={followUps.refresh}
        />

        <section className="section-grid grid gap-6 xl:grid-cols-2">
          <AssetPackCard
            assetPack={latestAssetPack}
            loading={assetPacks.loading}
            error={assetPacks.error}
          />
          <LaunchPlanCard
            launchPlan={latestLaunchPlan}
            loading={launchPlans.loading}
            error={launchPlans.error}
          />
        </section>
      </div>
    </main>
  );
}
