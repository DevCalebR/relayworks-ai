"use client";

import type { FormEvent, ReactNode } from "react";
import { startTransition, useEffect, useState } from "react";

import {
  API_BASE_URL,
  PROJECT_ID,
  compareOpportunities,
  createLead,
  createBatchOutreachDrafts,
  createOutreachDraft,
  discoverCandidateLeads,
  formatDateTime,
  formatWebsite,
  generateAssetPack,
  generateLaunchPlan,
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
  runOpportunityAnalysis,
  sortNewestFirst,
  type AssetPack,
  type BackendStatusResponse,
  type CandidateLead,
  type CandidateStatus,
  type FollowUpQueueItem,
  type LaunchPlan,
  type Lead,
  type LeadStatus,
  type OperatorMode,
  type OpportunityComparison,
  type OutreachRecord,
  type OutreachStatus,
  type PipelineMetrics,
} from "@/lib/api";

const DEFAULT_DISCOVERY_TARGET =
  "Seed to Series B B2B SaaS companies likely to care about win-loss analysis, revenue operations, sales process improvement, and closed-lost learning loops";
const DEFAULT_ANALYSIS_OBJECTIVE =
  "Find the best fast-to-market profitable AI operator business opportunity";
const OPERATOR_MODES: OperatorMode[] = [
  "research_operator",
  "content_operator",
  "leadgen_operator",
  "product_operator",
];
type ComparisonModeFilter = OperatorMode | "all";

const WORKFLOW_STEPS = [
  "Run Opportunity Analysis",
  "Generate Launch Plan",
  "Generate Asset Pack",
  "Discover Candidates",
  "Import Leads",
  "Create Drafts",
  "Send Manually",
  "Mark Sent",
  "Follow Up",
];

const LEAD_STATUSES: LeadStatus[] = [
  "new",
  "contacted",
  "replied",
  "interested",
  "closed",
];

const OUTREACH_STATUSES: OutreachStatus[] = ["draft", "sent", "replied", "ignored"];

type ManualLeadFormState = {
  companyName: string;
  contactName: string;
  contactEmail: string;
  industry: string;
  website: string;
  companyDescription: string;
  notes: string;
};

const EMPTY_MANUAL_LEAD_FORM: ManualLeadFormState = {
  companyName: "",
  contactName: "",
  contactEmail: "",
  industry: "",
  website: "",
  companyDescription: "",
  notes: "",
};

function humanize(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function isValidEmailAddress(value: string): boolean {
  return value.includes("@") && value.includes(".");
}

function getWebsiteValidationMessage(value: string): string | null {
  const trimmedValue = value.trim();
  if (!trimmedValue) {
    return null;
  }

  const normalizedValue = trimmedValue.replace(/^https?:\/\//, "");
  if (!normalizedValue) {
    return "Add a website like relayworks.ai or leave the field empty.";
  }

  if (/\s/.test(trimmedValue)) {
    return "Website should not contain spaces.";
  }

  return null;
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong while loading this section.";
}

function getFriendlyGenerationError(error: unknown, action: "launch-plan" | "asset-pack"): string {
  const message = toErrorMessage(error);
  const normalized = message.toLowerCase();

  if (action === "launch-plan") {
    if (
      normalized.includes("could not resolve a launch-plan source") ||
      normalized.includes("could not resolve a launch plan source")
    ) {
      return "No top opportunity found yet. Run opportunity analysis first.";
    }
    return message;
  }

  if (
    normalized.includes("no launch plan found for project") ||
    normalized.includes("launch plan not found for project")
  ) {
    return "Generate a launch plan first.";
  }

  return message;
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

function GenerationControlCard({
  eyebrow,
  title,
  description,
  buttonLabel,
  loadingLabel,
  disabled,
  loading,
  notice,
  error,
  onClick,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  buttonLabel: string;
  loadingLabel: string;
  disabled?: boolean;
  loading: boolean;
  notice: string | null;
  error: string | null;
  onClick: () => void;
  children?: ReactNode;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow={eyebrow}
        title={title}
        description={description}
      />
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}
      {children}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        className="inline-flex items-center justify-center rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? loadingLabel : buttonLabel}
      </button>
    </Card>
  );
}

function OpportunitySummaryCard({
  comparison,
  loading,
  error,
  selectedMode,
  onModeChange,
  onRefresh,
}: {
  comparison: OpportunityComparison | null;
  loading: boolean;
  error: string | null;
  selectedMode: ComparisonModeFilter;
  onModeChange: (mode: ComparisonModeFilter) => void;
  onRefresh: () => void;
}) {
  const topOpportunity = comparison?.top_opportunity ?? null;
  const rankedOpportunities = comparison?.ranked_opportunities ?? [];

  return (
    <Card className="space-y-6">
      <SectionHeading
        eyebrow="Opportunity"
        title="Top Opportunity"
        description="Compare recent opportunity analysis runs, review the current best option, and keep launch-plan generation anchored to the strongest idea on screen."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-2 rounded-full border border-border bg-white/70 px-3 py-2 text-sm text-foreground">
              <span className="font-semibold">Mode</span>
              <select
                value={selectedMode}
                onChange={(event) => onModeChange(event.target.value as ComparisonModeFilter)}
                className="bg-transparent text-sm outline-none"
              >
                <option value="all">All modes</option>
                {OPERATOR_MODES.map((mode) => (
                  <option key={mode} value={mode}>
                    {humanize(mode)}
                  </option>
                ))}
              </select>
            </label>
            <RefreshButton
              label="top opportunity"
              onClick={onRefresh}
              disabled={loading}
            />
          </div>
        }
      />
      {error ? <DataError message={error} /> : null}
      {comparison ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <StatTile label="Analysis runs" value={comparison.total_runs} />
          <StatTile label="Ranked opportunities" value={comparison.total_opportunities} accent />
        </div>
      ) : null}
      {!comparison && loading ? (
        <p className="text-sm text-muted">Loading opportunity comparison...</p>
      ) : null}
      {!topOpportunity && !loading && !error ? (
        <EmptyState
          title="No opportunity analysis found yet."
          description="Run an analysis first to compare opportunities and generate a launch plan from the current top result."
        />
      ) : null}
      {topOpportunity ? (
        <div className="space-y-5">
          <div className="rounded-[26px] border border-emerald-200 bg-emerald-50/70 p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge label="Current top opportunity" tone="bg-emerald-200 text-emerald-950" />
                  <Badge
                    label={`Opportunity ${topOpportunity.opportunity_score}/10`}
                    tone="bg-white text-stone-900"
                  />
                  <Badge
                    label={`Confidence ${topOpportunity.confidence_score}/10`}
                    tone="bg-white text-stone-900"
                  />
                  <Badge label={humanize(topOpportunity.mode)} tone="bg-white text-stone-900" />
                </div>
                <div>
                  <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                    {topOpportunity.title}
                  </h3>
                  <p className="mt-1 text-sm text-muted">
                    Run {topOpportunity.run_id} · {formatDateTime(topOpportunity.created_at)}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <InfoField label="Niche" value={topOpportunity.niche} />
              <InfoField label="Target customer" value={topOpportunity.target_customer} />
              <InfoField label="Core problem" value={topOpportunity.core_problem} />
              <InfoField label="Offer" value={topOpportunity.offer} />
              <InfoField label="MVP" value={topOpportunity.mvp} />
              <InfoField
                label="Distribution channel"
                value={topOpportunity.distribution_channel}
              />
              <InfoField
                label="Monetization model"
                value={topOpportunity.monetization_model}
              />
            </div>
            <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
              <InfoField
                label="Reasoning"
                value={topOpportunity.reasoning}
                preserveWhitespace
              />
              <div className="space-y-2">
                <p className="font-mono text-[11px] tracking-[0.18em] uppercase text-muted">
                  Next actions
                </p>
                <div className="rounded-3xl border border-border bg-white/75 px-4 py-4">
                  <ol className="space-y-2 text-sm leading-6 text-foreground">
                    {topOpportunity.next_actions.map((action, index) => (
                      <li key={`${topOpportunity.run_id}-${action}`} className="flex gap-3">
                        <span className="font-semibold text-emerald-900">{index + 1}.</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </div>
          </div>

          {rankedOpportunities.length > 0 ? (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">Ranked opportunities</h3>
                <p className="text-sm text-muted">Compact view of the current comparison set.</p>
              </div>
              <div className="space-y-3">
                {rankedOpportunities.map((opportunity, index) => (
                  <article
                    key={`${opportunity.run_id}-${opportunity.title}-${index}`}
                    className="rounded-3xl border border-border bg-white/65 px-4 py-4"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                      <div className="flex items-start gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-stone-50">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-base font-semibold text-foreground">
                            {opportunity.title}
                          </p>
                          <p className="text-sm text-muted">{opportunity.niche}</p>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          label={`Opportunity ${opportunity.opportunity_score}/10`}
                          tone="bg-emerald-100 text-emerald-900"
                        />
                        <Badge
                          label={`Confidence ${opportunity.confidence_score}/10`}
                          tone="bg-sky-100 text-sky-900"
                        />
                        <Badge
                          label={humanize(opportunity.mode)}
                          tone="bg-stone-200 text-stone-900"
                        />
                        <Badge
                          label={`Run ${opportunity.run_id}`}
                          tone="bg-white text-stone-900"
                        />
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

function OpportunityAnalysisCard({
  objective,
  mode,
  numOpportunities,
  loading,
  notice,
  error,
  onObjectiveChange,
  onModeChange,
  onNumOpportunitiesChange,
  onSubmit,
}: {
  objective: string;
  mode: OperatorMode;
  numOpportunities: number;
  loading: boolean;
  notice: string | null;
  error: string | null;
  onObjectiveChange: (value: string) => void;
  onModeChange: (mode: OperatorMode) => void;
  onNumOpportunitiesChange: (value: number) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Card className="space-y-6">
      <SectionHeading
        eyebrow="Opportunity"
        title="Run Opportunity Analysis"
        description="Start the operator workflow visually. This form calls the existing backend endpoint and refreshes the current opportunity comparison after a successful run."
      />
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-foreground">Objective</span>
          <textarea
            value={objective}
            onChange={(event) => onObjectiveChange(event.target.value)}
            rows={6}
            className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none transition focus:border-emerald-500"
          />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Mode</span>
            <select
              value={mode}
              onChange={(event) => onModeChange(event.target.value as OperatorMode)}
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            >
              {OPERATOR_MODES.map((option) => (
                <option key={option} value={option}>
                  {humanize(option)}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Number of opportunities</span>
            <input
              type="number"
              min={1}
              max={5}
              value={numOpportunities}
              onChange={(event) =>
                onNumOpportunitiesChange(
                  Math.min(5, Math.max(1, Number(event.target.value) || 1)),
                )
              }
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
        </div>
        <InlineNotice tone="info">
          The dashboard sends a simple form payload to <span className="font-mono">POST /agents/run</span>. No JSON editing required.
        </InlineNotice>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Running analysis..." : "Run Analysis"}
        </button>
      </form>
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

function ManualLeadFormCard({
  form,
  loading,
  notice,
  error,
  fieldError,
  onChange,
  onSubmit,
}: {
  form: ManualLeadFormState;
  loading: boolean;
  notice: string | null;
  error: string | null;
  fieldError: string | null;
  onChange: (field: keyof ManualLeadFormState, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Leads"
        title="Add Lead Manually"
        description="Add a real lead directly into the current project without curl, seed file edits, or candidate import."
      />
      <InlineNotice tone="warning">
        Only add leads you are allowed to contact. RelayWorks creates drafts, but you still send manually.
      </InlineNotice>
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}
      {fieldError ? <InlineNotice tone="error">{fieldError}</InlineNotice> : null}
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-foreground">
            Company name <span className="text-rose-700">*</span>
          </span>
          <input
            type="text"
            value={form.companyName}
            onChange={(event) => onChange("companyName", event.target.value)}
            placeholder="Acme Industrial"
            className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
          />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Contact name</span>
            <input
              type="text"
              value={form.contactName}
              onChange={(event) => onChange("contactName", event.target.value)}
              placeholder="Jordan Lee"
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Contact email</span>
            <input
              type="text"
              value={form.contactEmail}
              onChange={(event) => onChange("contactEmail", event.target.value)}
              placeholder="jordan@acme.com"
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Industry</span>
            <input
              type="text"
              value={form.industry}
              onChange={(event) => onChange("industry", event.target.value)}
              placeholder="Manufacturing"
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Website</span>
            <input
              type="text"
              value={form.website}
              onChange={(event) => onChange("website", event.target.value)}
              placeholder="acme.com"
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
        </div>
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-foreground">Company description</span>
          <textarea
            value={form.companyDescription}
            onChange={(event) => onChange("companyDescription", event.target.value)}
            rows={4}
            placeholder="What the company does and why it fits the offer."
            className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none transition focus:border-emerald-500"
          />
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-foreground">Notes</span>
          <textarea
            value={form.notes}
            onChange={(event) => onChange("notes", event.target.value)}
            rows={4}
            placeholder="Anything helpful for manual outreach later."
            className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none transition focus:border-emerald-500"
          />
        </label>
        <p className="text-xs leading-5 text-muted">
          Project: <span className="font-mono">{PROJECT_ID}</span> · Status:{" "}
          <span className="font-mono">new</span> · Dedupe: <span className="font-mono">true</span>
        </p>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Adding lead..." : "Add Lead"}
        </button>
      </form>
    </Card>
  );
}

function LeadsTable({
  leads,
  loading,
  error,
  notice,
  actionError,
  busyLeadId,
  batchLoading,
  highlightedLeadId,
  onRefresh,
  onCreateDraft,
  onCreateDraftsForNewLeads,
}: {
  leads: Lead[] | null;
  loading: boolean;
  error: string | null;
  notice: string | null;
  actionError: string | null;
  busyLeadId: string | null;
  batchLoading: boolean;
  highlightedLeadId: string | null;
  onRefresh: () => void;
  onCreateDraft: (leadId: string) => void;
  onCreateDraftsForNewLeads: () => void;
}) {
  const sortedLeads = leads ? sortNewestFirst(leads) : [];
  const newLeadCount = sortedLeads.filter((lead) => lead.status === "new").length;

  useEffect(() => {
    if (!highlightedLeadId || !leads || leads.length === 0) {
      return;
    }

    const row = document.getElementById(`lead-row-${highlightedLeadId}`);
    row?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightedLeadId, leads]);

  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Leads"
        title="Imported leads"
        description="These are the leads already in the working pipeline. New leads can generate email drafts from the latest asset pack, which makes the candidate-to-draft workflow visible in one place."
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onCreateDraftsForNewLeads}
              disabled={batchLoading}
              className="inline-flex items-center justify-center rounded-full bg-emerald-900 px-4 py-2 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {batchLoading ? "Creating drafts..." : "Create Drafts for New Leads"}
            </button>
            <RefreshButton label="leads" onClick={onRefresh} disabled={loading} />
          </div>
        }
      />
      <InlineNotice tone="info">
        RelayWorks does not send emails automatically. It only creates drafts. Send
        manually, then click Mark as Sent.
      </InlineNotice>
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {actionError ? <InlineNotice tone="error">{actionError}</InlineNotice> : null}
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
                <th className="px-3">Drafts</th>
              </tr>
            </thead>
            <tbody>
              {sortedLeads.map((lead) => (
                <tr
                  key={lead.id}
                  id={`lead-row-${lead.id}`}
                  className={`rounded-3xl text-sm text-foreground ${
                    highlightedLeadId === lead.id
                      ? "bg-emerald-50/95 ring-1 ring-emerald-300"
                      : "bg-white/65"
                  }`}
                >
                  <td className="rounded-l-3xl px-3 py-4 font-semibold">{lead.company_name}</td>
                  <td className="px-3 py-4">{lead.contact_name || "No verified contact yet"}</td>
                  <td className="px-3 py-4">{lead.contact_email.trim() || "No email yet"}</td>
                  <td className="px-3 py-4">
                    <Badge label={humanize(lead.status)} tone={getStatusTone(lead.status)} />
                  </td>
                  <td className="px-3 py-4">{lead.industry || "Unknown"}</td>
                  <td className="px-3 py-4">{formatWebsite(lead.website)}</td>
                  <td className="px-3 py-4">{formatDateTime(lead.created_at)}</td>
                  <td className="rounded-r-3xl px-3 py-4">
                    <div className="space-y-2">
                      {lead.status === "new" ? (
                        <button
                          type="button"
                          disabled={busyLeadId === lead.id}
                          onClick={() => onCreateDraft(lead.id)}
                          className="rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {busyLeadId === lead.id ? "Creating..." : "Create Draft"}
                        </button>
                      ) : (
                        <span className="text-sm text-muted">
                          {lead.status === "contacted"
                            ? "Already contacted"
                            : "Not available"}
                        </span>
                      )}
                      {highlightedLeadId === lead.id ? (
                        <p className="max-w-[18rem] text-xs font-medium leading-5 text-emerald-900">
                          Next: create an outreach draft for this lead.
                        </p>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {leads && leads.length > 0 ? (
        <p className="text-sm text-muted">
          {newLeadCount === 0
            ? "No new leads need drafts right now."
            : `${newLeadCount} new lead${newLeadCount === 1 ? "" : "s"} can generate drafts from the latest asset pack.`}
        </p>
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

  const [analysisObjective, setAnalysisObjective] = useState(DEFAULT_ANALYSIS_OBJECTIVE);
  const [analysisMode, setAnalysisMode] = useState<OperatorMode>("research_operator");
  const [analysisNumOpportunities, setAnalysisNumOpportunities] = useState(3);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisNotice, setAnalysisNotice] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [comparisonMode, setComparisonMode] = useState<ComparisonModeFilter>("all");
  const [opportunityComparison, setOpportunityComparison] =
    useState<OpportunityComparison | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(true);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [candidateNotice, setCandidateNotice] = useState<string | null>(null);
  const [generationNotice, setGenerationNotice] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [assetPackNotice, setAssetPackNotice] = useState<string | null>(null);
  const [assetPackError, setAssetPackError] = useState<string | null>(null);
  const [leadNotice, setLeadNotice] = useState<string | null>(null);
  const [leadActionError, setLeadActionError] = useState<string | null>(null);
  const [manualLeadNotice, setManualLeadNotice] = useState<string | null>(null);
  const [manualLeadError, setManualLeadError] = useState<string | null>(null);
  const [manualLeadForm, setManualLeadForm] = useState<ManualLeadFormState>(
    EMPTY_MANUAL_LEAD_FORM,
  );
  const [manualLeadFieldError, setManualLeadFieldError] = useState<string | null>(null);
  const [creatingLead, setCreatingLead] = useState(false);
  const [highlightedLeadId, setHighlightedLeadId] = useState<string | null>(null);
  const [outreachNotice, setOutreachNotice] = useState<string | null>(null);
  const [candidateActionError, setCandidateActionError] = useState<string | null>(null);
  const [outreachActionError, setOutreachActionError] = useState<string | null>(null);
  const [busyCandidateId, setBusyCandidateId] = useState<string | null>(null);
  const [busyLeadId, setBusyLeadId] = useState<string | null>(null);
  const [busyOutreachId, setBusyOutreachId] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [generatingLaunchPlan, setGeneratingLaunchPlan] = useState(false);
  const [generatingAssetPack, setGeneratingAssetPack] = useState(false);
  const [creatingBatchDrafts, setCreatingBatchDrafts] = useState(false);
  const [target, setTarget] = useState(DEFAULT_DISCOVERY_TARGET);
  const [count, setCount] = useState(5);

  const latestAssetPack = assetPacks.data ? getLatestRecord(assetPacks.data) : null;
  const latestLaunchPlan = launchPlans.data ? getLatestRecord(launchPlans.data) : null;
  const currentTopOpportunity = opportunityComparison?.top_opportunity ?? null;
  const currentLaunchPlanMode =
    comparisonMode === "all" ? undefined : comparisonMode;

  async function refreshOpportunityComparison(mode: ComparisonModeFilter = comparisonMode) {
    setComparisonLoading(true);
    try {
      const next = await compareOpportunities(mode === "all" ? undefined : mode);
      setOpportunityComparison(next);
      setComparisonError(null);
    } catch (error) {
      setComparisonError(toErrorMessage(error));
    } finally {
      setComparisonLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadComparison() {
      setComparisonLoading(true);
      try {
        const next = await compareOpportunities(
          comparisonMode === "all" ? undefined : comparisonMode,
        );
        if (!active) {
          return;
        }
        setOpportunityComparison(next);
        setComparisonError(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setComparisonError(toErrorMessage(error));
      } finally {
        if (active) {
          setComparisonLoading(false);
        }
      }
    }

    void loadComparison();

    return () => {
      active = false;
    };
  }, [comparisonMode]);

  async function handleRunOpportunityAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRunningAnalysis(true);
    setAnalysisNotice(null);
    setAnalysisError(null);

    const trimmedObjective = analysisObjective.trim();
    if (!trimmedObjective) {
      setAnalysisError("Add an objective before running opportunity analysis.");
      setRunningAnalysis(false);
      return;
    }

    try {
      const run = await runOpportunityAnalysis({
        objective: trimmedObjective,
        mode: analysisMode,
        numOpportunities: analysisNumOpportunities,
      });
      setAnalysisNotice(
        `Analysis complete for ${humanize(run.mode)}. Top opportunity refreshed below. You can now generate a launch plan.`,
      );
      if (comparisonMode !== run.mode) {
        setComparisonMode(run.mode);
      } else {
        startTransition(() => {
          void refreshOpportunityComparison(run.mode);
        });
      }
    } catch (error) {
      setAnalysisError(toErrorMessage(error));
    } finally {
      setRunningAnalysis(false);
    }
  }

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
      setCandidateNotice(
        "Candidate imported. You can now create an outreach draft from the Leads section.",
      );
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

  async function handleGenerateLaunchPlan() {
    if (comparisonLoading) {
      setGenerationError("Top opportunity is still loading. Try again in a moment.");
      setGenerationNotice(null);
      return;
    }

    if (!currentTopOpportunity) {
      setGenerationError(
        comparisonError ?? "No top opportunity found yet. Run opportunity analysis first.",
      );
      setGenerationNotice(null);
      return;
    }

    setGeneratingLaunchPlan(true);
    setGenerationNotice(null);
    setGenerationError(null);

    try {
      const launchPlan = await generateLaunchPlan(currentLaunchPlanMode);
      setGenerationNotice(
        `Launch plan generated from ${currentTopOpportunity.title}: ${launchPlan.headline}`,
      );
      startTransition(() => {
        void launchPlans.refresh();
      });
    } catch (error) {
      setGenerationError(getFriendlyGenerationError(error, "launch-plan"));
    } finally {
      setGeneratingLaunchPlan(false);
    }
  }

  async function handleGenerateAssetPack() {
    setGeneratingAssetPack(true);
    setAssetPackNotice(null);
    setAssetPackError(null);

    try {
      const assetPack = await generateAssetPack();
      setAssetPackNotice(`Asset pack generated: ${assetPack.headline}`);
      startTransition(() => {
        void assetPacks.refresh();
      });
    } catch (error) {
      setAssetPackError(getFriendlyGenerationError(error, "asset-pack"));
    } finally {
      setGeneratingAssetPack(false);
    }
  }

  function updateManualLeadForm(field: keyof ManualLeadFormState, value: string) {
    setManualLeadForm((current) => ({
      ...current,
      [field]: value,
    }));

    if (manualLeadFieldError) {
      setManualLeadFieldError(null);
    }
    if (manualLeadError) {
      setManualLeadError(null);
    }
  }

  async function handleCreateLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreatingLead(true);
    setManualLeadNotice(null);
    setManualLeadError(null);
    setManualLeadFieldError(null);

    const companyName = manualLeadForm.companyName.trim();
    const contactName = manualLeadForm.contactName.trim();
    const contactEmail = manualLeadForm.contactEmail.trim();
    const industry = manualLeadForm.industry.trim();
    const website = manualLeadForm.website.trim();
    const companyDescription = manualLeadForm.companyDescription.trim();
    const notes = manualLeadForm.notes.trim();

    if (!companyName) {
      setManualLeadFieldError("Add a company name before creating the lead.");
      setCreatingLead(false);
      return;
    }

    if (contactEmail && !isValidEmailAddress(contactEmail)) {
      setManualLeadFieldError("Add a valid-looking email address or leave it empty.");
      setCreatingLead(false);
      return;
    }

    const websiteValidationMessage = getWebsiteValidationMessage(website);
    if (websiteValidationMessage) {
      setManualLeadFieldError(websiteValidationMessage);
      setCreatingLead(false);
      return;
    }

    try {
      const lead = await createLead({
        companyName,
        contactName,
        contactEmail,
        industry,
        website,
        companyDescription,
        notes,
      });

      setHighlightedLeadId(lead.id);
      await Promise.all([leads.refresh(), metrics.refresh()]);

      if (lead.deduped) {
        setManualLeadNotice("Lead already exists. Showing the existing lead.");
        return;
      }

      setManualLeadNotice("Lead added. Next: create an outreach draft for this lead.");
      setManualLeadForm(EMPTY_MANUAL_LEAD_FORM);
    } catch (error) {
      setManualLeadError(toErrorMessage(error));
    } finally {
      setCreatingLead(false);
    }
  }

  async function handleCreateDraft(leadId: string) {
    setBusyLeadId(leadId);
    setLeadNotice(null);
    setLeadActionError(null);

    if (!latestAssetPack) {
      setLeadActionError("Generate an asset pack first.");
      setBusyLeadId(null);
      return;
    }

    try {
      const outreachDraft = await createOutreachDraft({
        leadId,
        assetPackId: latestAssetPack.id,
      });
      setLeadNotice(
        outreachDraft.deduped
          ? "A matching draft already existed for that lead."
          : "Draft created for the selected lead.",
      );
      startTransition(() => {
        void Promise.all([outreach.refresh(), leads.refresh(), metrics.refresh()]);
      });
    } catch (error) {
      setLeadActionError(toErrorMessage(error));
    } finally {
      setBusyLeadId(null);
    }
  }

  async function handleCreateDraftsForNewLeads() {
    setCreatingBatchDrafts(true);
    setLeadNotice(null);
    setLeadActionError(null);

    if (!latestAssetPack) {
      setLeadActionError("Generate an asset pack first.");
      setCreatingBatchDrafts(false);
      return;
    }

    const newLeadIds = (leads.data ?? [])
      .filter((lead) => lead.status === "new")
      .map((lead) => lead.id);

    if (newLeadIds.length === 0) {
      setLeadNotice("No new leads need drafts.");
      setCreatingBatchDrafts(false);
      return;
    }

    try {
      const outreachDrafts = await createBatchOutreachDrafts({
        leadIds: newLeadIds,
        assetPackId: latestAssetPack.id,
      });
      const dedupedCount = outreachDrafts.filter((draft) => draft.deduped).length;
      const createdCount = outreachDrafts.length - dedupedCount;
      setLeadNotice(
        `Draft batch complete. ${createdCount} created, ${dedupedCount} deduped.`,
      );
      startTransition(() => {
        void Promise.all([outreach.refresh(), metrics.refresh(), leads.refresh()]);
      });
    } catch (error) {
      setLeadActionError(toErrorMessage(error));
    } finally {
      setCreatingBatchDrafts(false);
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
                    RelayWorks AI helps you run opportunity analysis, turn the top result
                    into a launch plan, build messaging assets, discover candidate leads,
                    import leads, generate outreach drafts, manually send them, and track
                    follow-ups.
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

        <section className="section-grid grid gap-6 xl:grid-cols-2">
          <OpportunityAnalysisCard
            objective={analysisObjective}
            mode={analysisMode}
            numOpportunities={analysisNumOpportunities}
            loading={runningAnalysis}
            notice={analysisNotice}
            error={analysisError}
            onObjectiveChange={setAnalysisObjective}
            onModeChange={setAnalysisMode}
            onNumOpportunitiesChange={setAnalysisNumOpportunities}
            onSubmit={handleRunOpportunityAnalysis}
          />
          <OpportunitySummaryCard
            comparison={opportunityComparison}
            loading={comparisonLoading}
            error={comparisonError}
            selectedMode={comparisonMode}
            onModeChange={setComparisonMode}
            onRefresh={() => {
              void refreshOpportunityComparison();
            }}
          />
        </section>

        <section className="section-grid grid gap-6 xl:grid-cols-2">
          <GenerationControlCard
            eyebrow="Launch"
            title="Generate Launch Plan"
            description="Use the current top opportunity to generate a fresh launch plan without writing JSON by hand."
            buttonLabel="Generate Launch Plan"
            loadingLabel="Generating launch plan..."
            disabled={!comparisonError && (comparisonLoading || !currentTopOpportunity)}
            loading={generatingLaunchPlan}
            notice={generationNotice}
            error={generationError}
            onClick={handleGenerateLaunchPlan}
          >
            <InlineNotice tone="info">
              Launch plans are generated from the current top opportunity.
            </InlineNotice>
            {currentTopOpportunity ? (
              <div className="rounded-3xl border border-border bg-white/65 px-4 py-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
                  Current source
                </p>
                <p className="mt-2 text-base font-semibold text-foreground">
                  {currentTopOpportunity.title}
                </p>
                <p className="mt-1 text-sm text-muted">
                  {humanize(currentTopOpportunity.mode)} · Run {currentTopOpportunity.run_id}
                </p>
              </div>
            ) : (
              <InlineNotice tone="warning">
                No top opportunity found yet. Run opportunity analysis first.
              </InlineNotice>
            )}
          </GenerationControlCard>
          <GenerationControlCard
            eyebrow="Assets"
            title="Generate Asset Pack"
            description="Use the latest launch plan to create the latest messaging package that powers outreach draft generation."
            buttonLabel="Generate Asset Pack"
            loadingLabel="Generating asset pack..."
            loading={generatingAssetPack}
            notice={assetPackNotice}
            error={assetPackError}
            onClick={handleGenerateAssetPack}
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

        <section className="section-grid grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
          <ManualLeadFormCard
            form={manualLeadForm}
            loading={creatingLead}
            notice={manualLeadNotice}
            error={manualLeadError}
            fieldError={manualLeadFieldError}
            onChange={updateManualLeadForm}
            onSubmit={handleCreateLead}
          />
          <LeadsTable
            leads={leads.data}
            loading={leads.loading}
            error={leads.error}
            notice={leadNotice}
            actionError={leadActionError}
            busyLeadId={busyLeadId}
            batchLoading={creatingBatchDrafts}
            highlightedLeadId={highlightedLeadId}
            onRefresh={leads.refresh}
            onCreateDraft={handleCreateDraft}
            onCreateDraftsForNewLeads={handleCreateDraftsForNewLeads}
          />
        </section>

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
