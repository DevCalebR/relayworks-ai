"use client";

import type { FormEvent, ReactNode } from "react";
import { startTransition, useEffect, useState } from "react";

import {
  API_BASE_URL,
  PROJECT_ID,
  compareOpportunities,
  createBatchOutreachDrafts,
  createLead,
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
const DEMO_PROJECT_ID = "proj_952a38d1f320";
const OPERATOR_MODES: OperatorMode[] = [
  "research_operator",
  "content_operator",
  "leadgen_operator",
  "product_operator",
];
const OUTREACH_STATUSES: OutreachStatus[] = ["draft", "sent", "replied", "ignored"];

type DashboardTab =
  | "home"
  | "opportunity"
  | "leads"
  | "drafts"
  | "followups"
  | "assets"
  | "metrics"
  | "advanced";

type ComparisonModeFilter = OperatorMode | "all";
type WorkflowState = "done" | "current" | "not_started";

type ManualLeadFormState = {
  companyName: string;
  contactName: string;
  contactEmail: string;
  industry: string;
  website: string;
  companyDescription: string;
  notes: string;
};

type NextStepRecommendation = {
  title: string;
  description: string;
  ctaLabel: string;
  tab: DashboardTab;
  sectionId?: string;
  refreshOnly?: boolean;
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

const DASHBOARD_TABS: { id: DashboardTab; label: string }[] = [
  { id: "home", label: "Home" },
  { id: "opportunity", label: "Opportunity" },
  { id: "leads", label: "Leads" },
  { id: "drafts", label: "Drafts" },
  { id: "followups", label: "Follow-ups" },
  { id: "assets", label: "Assets" },
  { id: "metrics", label: "Metrics" },
  { id: "advanced", label: "Advanced" },
];

const WORKFLOW_LABELS = [
  {
    title: "Pick an opportunity",
    description: "Choose the business idea you want to pursue first.",
  },
  {
    title: "Generate launch plan",
    description: "Turn the best idea into a practical business plan.",
  },
  {
    title: "Generate asset pack",
    description: "Create your sales materials and messaging.",
  },
  {
    title: "Find or add leads",
    description: "Build the list of companies or people you may contact.",
  },
  {
    title: "Create drafts",
    description: "Generate first-pass outreach messages.",
  },
  {
    title: "Send manually",
    description: "Copy the message and send it yourself.",
  },
  {
    title: "Mark sent",
    description: "Tell the app which message you already sent.",
  },
  {
    title: "Follow up",
    description: "Check replies and decide the next manual step.",
  },
];

function classNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

function humanize(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural;
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
      return "No top opportunity found yet. Find Business Ideas first.";
    }
    return message;
  }

  if (
    normalized.includes("no launch plan found for project") ||
    normalized.includes("launch plan not found for project")
  ) {
    return "Create a Business Plan first.";
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
      return "bg-stone-200 text-stone-800";
    default:
      return "bg-stone-200 text-stone-800";
  }
}

function getWorkflowTone(state: WorkflowState): string {
  switch (state) {
    case "done":
      return "bg-emerald-100 text-emerald-900";
    case "current":
      return "bg-amber-100 text-amber-950";
    default:
      return "bg-stone-200 text-stone-700";
  }
}

function getWorkflowLabel(state: WorkflowState): string {
  switch (state) {
    case "done":
      return "Done";
    case "current":
      return "Current";
    default:
      return "Not started";
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

function Card({
  id,
  className,
  highlighted,
  children,
}: {
  id?: string;
  className?: string;
  highlighted?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      className={classNames(
        "glass-panel rounded-[28px] p-6 scroll-mt-28 transition",
        highlighted && "ring-2 ring-emerald-400 ring-offset-2 ring-offset-transparent",
        className,
      )}
    >
      {children}
    </section>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  technicalLabel,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
  technicalLabel?: string;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-2">
        <p className="font-mono text-[11px] tracking-[0.24em] uppercase text-muted">
          {eyebrow}
        </p>
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
            {technicalLabel ? <Badge label={technicalLabel} tone="bg-white/80 text-stone-700" /> : null}
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted">{description}</p>
        </div>
      </div>
      {action}
    </div>
  );
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
  action,
  secondaryValue,
}: {
  label: string;
  value: string;
  preserveWhitespace?: boolean;
  action?: ReactNode;
  secondaryValue?: string;
}) {
  return (
    <div className="space-y-2 rounded-3xl border border-border bg-white/60 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="font-mono text-[11px] tracking-[0.18em] uppercase text-muted">{label}</p>
        {action}
      </div>
      <p
        className={classNames(
          "text-sm leading-6 text-foreground",
          preserveWhitespace && "whitespace-pre-wrap",
        )}
      >
        {value}
      </p>
      {secondaryValue ? <p className="text-xs leading-5 text-muted">{secondaryValue}</p> : null}
    </div>
  );
}

function DataError({ message }: { message: string }) {
  return <InlineNotice tone="error">{message}</InlineNotice>;
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
      className="inline-flex items-center justify-center rounded-full border border-border bg-white/80 px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
    >
      {disabled ? `Refreshing ${label}...` : `Refresh ${label}`}
    </button>
  );
}

function PrimaryButton({
  label,
  onClick,
  disabled,
  loadingLabel,
  loading,
  fullWidth,
  type = "button",
}: {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  loadingLabel?: string;
  loading?: boolean;
  fullWidth?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={classNames(
        "inline-flex items-center justify-center rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60",
        fullWidth && "w-full",
      )}
    >
      {loading ? loadingLabel ?? `${label}...` : label}
    </button>
  );
}

function CopyButton({
  copyKey,
  copiedKey,
  value,
  onCopy,
}: {
  copyKey: string;
  copiedKey: string | null;
  value: string;
  onCopy: (copyKey: string, value: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onCopy(copyKey, value)}
      className="rounded-full border border-border bg-white px-3 py-1.5 text-xs font-semibold text-foreground transition hover:bg-stone-100"
    >
      {copiedKey === copyKey ? "Copied." : "Copy"}
    </button>
  );
}

function StatTile({
  label,
  value,
  accent,
  description,
}: {
  label: string;
  value: number;
  accent?: boolean;
  description?: string;
}) {
  return (
    <div
      className={classNames(
        "rounded-3xl border px-4 py-4",
        accent ? "border-emerald-200 bg-emerald-50/70" : "border-border bg-white/65",
      )}
    >
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
      {description ? <p className="mt-2 text-sm leading-6 text-muted">{description}</p> : null}
    </div>
  );
}

function TabButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classNames(
        "rounded-full px-4 py-2.5 text-sm font-semibold transition",
        active
          ? "bg-stone-900 text-stone-50 shadow-sm"
          : "bg-white/65 text-foreground hover:bg-white",
      )}
    >
      {label}
    </button>
  );
}

function ActionCard({
  id,
  highlighted,
  eyebrow,
  title,
  description,
  helperText,
  buttonLabel,
  loadingLabel,
  loading,
  disabled,
  notice,
  error,
  onClick,
  children,
  technicalLabel,
}: {
  id: string;
  highlighted?: boolean;
  eyebrow: string;
  title: string;
  description: string;
  helperText: string;
  buttonLabel: string;
  loadingLabel: string;
  loading: boolean;
  disabled?: boolean;
  notice: string | null;
  error: string | null;
  onClick: () => void;
  children?: ReactNode;
  technicalLabel?: string;
}) {
  return (
    <Card id={id} highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow={eyebrow}
        title={title}
        description={description}
        technicalLabel={technicalLabel}
      />
      <p className="text-sm leading-6 text-muted">{helperText}</p>
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}
      {children}
      <PrimaryButton
        label={buttonLabel}
        loadingLabel={loadingLabel}
        loading={loading}
        disabled={disabled}
        onClick={onClick}
      />
    </Card>
  );
}

function HomeStartHereCard({ demoMode }: { demoMode: boolean }) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Start Here"
        title="Start Here"
        description="RelayWorks helps you choose an offer, find or add leads, create outreach drafts, manually send them, and track follow-ups."
      />
      {demoMode ? (
        <InlineNotice tone="info">
          Demo/local mode: This dashboard is using local JSON data. Use the reset script if you
          want a clean demo state.
        </InlineNotice>
      ) : null}
      <p className="text-base leading-7 text-foreground">
        The app does not send emails for you. It creates drafts. You review and send them
        manually, then mark them as sent.
      </p>
    </Card>
  );
}

function NextStepCard({
  recommendation,
  onOpen,
  onRefreshBackend,
}: {
  recommendation: NextStepRecommendation;
  onOpen: (tab: DashboardTab, sectionId?: string) => void;
  onRefreshBackend: () => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Guidance"
        title="What should I do next?"
        description="This recommendation looks at the current project data and points you to the next best operator action."
      />
      <div className="rounded-[26px] border border-emerald-200 bg-emerald-50/70 p-5">
        <Badge label="Recommended next step" tone="bg-emerald-200 text-emerald-950" />
        <h3 className="mt-4 text-2xl font-semibold tracking-tight text-foreground">
          {recommendation.title}
        </h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{recommendation.description}</p>
        <div className="mt-5">
          <PrimaryButton
            label={recommendation.ctaLabel}
            onClick={() => {
              if (recommendation.refreshOnly) {
                onRefreshBackend();
                return;
              }
              onOpen(recommendation.tab, recommendation.sectionId);
            }}
          />
        </div>
      </div>
    </Card>
  );
}

function WorkflowChecklist({
  states,
}: {
  states: WorkflowState[];
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Checklist"
        title="Your Workflow"
        description="Move through these steps from left to right. The current step is the one RelayWorks thinks needs your attention next."
      />
      <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
        {WORKFLOW_LABELS.map((step, index) => (
          <article key={step.title} className="rounded-3xl border border-border bg-white/65 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-stone-50">
                  {index + 1}
                </span>
                <div>
                  <p className="text-base font-semibold text-foreground">{step.title}</p>
                </div>
              </div>
              <Badge label={getWorkflowLabel(states[index] ?? "not_started")} tone={getWorkflowTone(states[index] ?? "not_started")} />
            </div>
            <p className="mt-3 text-sm leading-6 text-muted">{step.description}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

function StatusCard({
  status,
  loading,
  error,
  highlighted,
}: {
  status: BackendStatusResponse | null;
  loading: boolean;
  error: string | null;
  highlighted?: boolean;
}) {
  return (
    <Card id="backend-status" highlighted={highlighted} className="space-y-4">
      <SectionHeading
        eyebrow="Backend"
        title="Backend Status"
        description="RelayWorks needs the local FastAPI backend running before anything else will work."
      />
      {error ? <DataError message={error} /> : null}
      {!status && loading ? <p className="text-sm text-muted">Checking backend status...</p> : null}
      {status ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge
              label={status.online ? "Online" : "Offline"}
              tone={status.online ? "bg-emerald-100 text-emerald-900" : "bg-rose-100 text-rose-900"}
            />
            <p className="font-mono text-xs text-muted">{API_BASE_URL}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <InfoField label="Root response" value={status.root.message} />
            <InfoField label="Health check" value={`status: ${status.health.status}`} />
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function HomeMetricsCard({
  candidateCount,
  leadCount,
  draftCount,
  followUpCount,
}: {
  candidateCount: number;
  leadCount: number;
  draftCount: number;
  followUpCount: number;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Overview"
        title="Key Metrics"
        description="These counts help you understand what is waiting for review right now."
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile label="Possible leads to review" value={candidateCount} />
        <StatTile label="Leads in pipeline" value={leadCount} accent />
        <StatTile label="Drafts waiting" value={draftCount} />
        <StatTile label="Follow-ups due" value={followUpCount} />
      </div>
    </Card>
  );
}

function HomeOpportunityCard({
  topOpportunity,
  loading,
  error,
  onOpenOpportunity,
}: {
  topOpportunity: OpportunityComparison["top_opportunity"];
  loading: boolean;
  error: string | null;
  onOpenOpportunity: () => void;
}) {
  return (
    <Card className="space-y-5">
      <SectionHeading
        eyebrow="Current Focus"
        title="Current Top Opportunity"
        description="This is the business idea the system would use for the next Business Plan."
      />
      {error ? <DataError message={error} /> : null}
      {!topOpportunity && loading ? <p className="text-sm text-muted">Loading opportunity data...</p> : null}
      {!topOpportunity && !loading && !error ? (
        <EmptyState
          title="No business idea selected yet"
          description="Go to the Opportunity tab and use Find Business Ideas to create a ranked list."
        />
      ) : null}
      {topOpportunity ? (
        <div className="space-y-4 rounded-[26px] border border-emerald-200 bg-emerald-50/70 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge label="Top opportunity" tone="bg-emerald-200 text-emerald-950" />
            <Badge label={`Score ${topOpportunity.opportunity_score}/10`} tone="bg-white text-stone-900" />
            <Badge label={`Confidence ${topOpportunity.confidence_score}/10`} tone="bg-white text-stone-900" />
          </div>
          <div>
            <h3 className="text-2xl font-semibold text-foreground">{topOpportunity.title}</h3>
            <p className="mt-1 text-sm text-muted">
              {topOpportunity.target_customer} · {formatDateTime(topOpportunity.created_at)}
            </p>
          </div>
          <p className="text-sm leading-6 text-muted">{topOpportunity.reasoning}</p>
          <PrimaryButton label="Open Opportunity Tab" onClick={onOpenOpportunity} />
        </div>
      ) : null}
    </Card>
  );
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
        eyebrow="Metrics"
        title="Pipeline Metrics"
        description="Use this tab to understand how many leads and messages are at each stage."
        action={<RefreshButton label="metrics" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!metrics && loading ? <p className="text-sm text-muted">Loading pipeline metrics...</p> : null}
      {metrics ? (
        <div className="space-y-5">
          <div>
            <h3 className="text-lg font-semibold text-foreground">Leads</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <StatTile label="New" value={metrics.lead_counts.new} description="Ready for draft creation." />
              <StatTile label="Contacted" value={metrics.lead_counts.contacted} description="Marked sent after manual outreach." />
              <StatTile label="Replied" value={metrics.lead_counts.replied} description="Someone responded." />
              <StatTile label="Interested" value={metrics.lead_counts.interested} description="Positive signal worth following up." />
              <StatTile label="Closed" value={metrics.lead_counts.closed} description="Completed or no longer active." />
              <StatTile label="Total leads" value={metrics.lead_counts.total} accent description="All leads in this project." />
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Messages</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <StatTile label="Drafts" value={metrics.outreach_counts.draft} description="Ready for manual review and sending." />
              <StatTile label="Sent" value={metrics.outreach_counts.sent} description="Marked sent after you delivered them yourself." />
              <StatTile label="Replied" value={metrics.outreach_counts.replied} description="Messages with a reply logged." />
              <StatTile label="Ignored" value={metrics.outreach_counts.ignored} description="Messages you do not plan to use." />
              <StatTile label="Total messages" value={metrics.outreach_counts.total} accent description="All message records in this project." />
            </div>
          </div>
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
  highlighted,
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
  highlighted?: boolean;
  onObjectiveChange: (value: string) => void;
  onModeChange: (mode: OperatorMode) => void;
  onNumOpportunitiesChange: (value: number) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Card id="find-business-ideas" highlighted={highlighted} className="space-y-6">
      <SectionHeading
        eyebrow="Opportunity"
        title="Find Business Ideas"
        description="Create a ranked set of possible businesses for this project."
        technicalLabel="Opportunity analysis"
      />
      <p className="text-sm leading-6 text-muted">
        Uses AI to suggest business opportunities and rank them.
      </p>
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-2">
          <span className="text-sm font-semibold text-foreground">What are you trying to find?</span>
          <textarea
            value={objective}
            onChange={(event) => onObjectiveChange(event.target.value)}
            rows={6}
            className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none transition focus:border-emerald-500"
          />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-foreground">Idea style</span>
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
            <span className="text-sm font-semibold text-foreground">How many ideas?</span>
            <input
              type="number"
              min={1}
              max={5}
              value={numOpportunities}
              onChange={(event) =>
                onNumOpportunitiesChange(Math.min(5, Math.max(1, Number(event.target.value) || 1)))
              }
              className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none transition focus:border-emerald-500"
            />
          </label>
        </div>
        <PrimaryButton
          type="submit"
          label="Find Business Ideas"
          loadingLabel="Finding business ideas..."
          loading={loading}
        />
      </form>
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
        description="Review the highest-ranked idea before creating the Business Plan."
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
            <RefreshButton label="opportunities" onClick={onRefresh} disabled={loading} />
          </div>
        }
      />
      {error ? <DataError message={error} /> : null}
      {!comparison && loading ? <p className="text-sm text-muted">Loading opportunity comparison...</p> : null}
      {!topOpportunity && !loading && !error ? (
        <EmptyState
          title="No ranked ideas yet"
          description="Find Business Ideas first to populate this section."
        />
      ) : null}
      {topOpportunity ? (
        <div className="space-y-5">
          <div className="rounded-[26px] border border-emerald-200 bg-emerald-50/70 p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge label="Current top opportunity" tone="bg-emerald-200 text-emerald-950" />
                  <Badge label={`Score ${topOpportunity.opportunity_score}/10`} tone="bg-white text-stone-900" />
                  <Badge label={`Confidence ${topOpportunity.confidence_score}/10`} tone="bg-white text-stone-900" />
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
              <InfoField label="Target customer" value={topOpportunity.target_customer} />
              <InfoField label="Core problem" value={topOpportunity.core_problem} />
              <InfoField label="Offer" value={topOpportunity.offer} />
              <InfoField label="Distribution channel" value={topOpportunity.distribution_channel} />
            </div>
            <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
              <InfoField label="Reasoning" value={topOpportunity.reasoning} preserveWhitespace />
              <div className="rounded-3xl border border-border bg-white/75 p-4">
                <p className="font-mono text-[11px] tracking-[0.18em] uppercase text-muted">
                  Suggested next actions
                </p>
                <ol className="mt-3 space-y-2 text-sm leading-6 text-foreground">
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

          {comparison ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <StatTile label="Analysis runs" value={comparison.total_runs} />
              <StatTile label="Ranked opportunities" value={comparison.total_opportunities} accent />
            </div>
          ) : null}

          {rankedOpportunities.length > 0 ? (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">Ranked ideas</h3>
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
                          <p className="text-base font-semibold text-foreground">{opportunity.title}</p>
                          <p className="text-sm text-muted">{opportunity.niche}</p>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge label={`Score ${opportunity.opportunity_score}/10`} tone="bg-emerald-100 text-emerald-900" />
                        <Badge label={`Confidence ${opportunity.confidence_score}/10`} tone="bg-sky-100 text-sky-900" />
                        <Badge label={humanize(opportunity.mode)} tone="bg-stone-200 text-stone-900" />
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
            <Badge label="Possible lead to review" tone="bg-amber-200 text-amber-950" />
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
              {busy ? "Working..." : "Import to Leads"}
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
        Discover Possible Leads suggests companies that might fit. Emails are not verified.
      </p>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <InfoField label="Email" value={candidate.contact_email?.trim() || "No verified email yet"} />
        <InfoField label="Industry" value={candidate.industry?.trim() || "Industry not listed"} />
        <InfoField label="Website" value={formatWebsite(candidate.website)} />
        <InfoField label="Source" value={candidate.lead_source?.trim() || "No source listed"} />
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <InfoField label="Why it could fit" value={candidate.fit_reason} />
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
  highlighted,
  onChange,
  onSubmit,
}: {
  form: ManualLeadFormState;
  loading: boolean;
  notice: string | null;
  error: string | null;
  fieldError: string | null;
  highlighted?: boolean;
  onChange: (field: keyof ManualLeadFormState, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Card id="manual-lead" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Leads"
        title="Add Lead Manually"
        description="Use this when you already know a company or person you want to contact."
      />
      <p className="text-sm leading-6 text-muted">
        Use this when you already know a company or person you want to contact.
      </p>
      <InlineNotice tone="warning">
        RelayWorks creates drafts, but you still send manually.
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
            placeholder="What the company does and why it could fit."
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
          Project: <span className="font-mono">{PROJECT_ID}</span> · New leads start in the
          <span className="font-semibold"> new</span> stage.
        </p>
        <PrimaryButton
          type="submit"
          label="Add Lead Manually"
          loadingLabel="Adding lead..."
          loading={loading}
        />
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
  highlighted,
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
  highlighted?: boolean;
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
    <Card id="leads-table" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Leads"
        title="Leads in Your Pipeline"
        description="These are the companies or contacts you can work on next."
        action={
          <div className="flex flex-wrap gap-2">
            <PrimaryButton
              label="Create Drafts for New Leads"
              loadingLabel="Creating drafts..."
              loading={batchLoading}
              onClick={onCreateDraftsForNewLeads}
            />
            <RefreshButton label="leads" onClick={onRefresh} disabled={loading} />
          </div>
        }
      />
      <p className="text-sm leading-6 text-muted">
        Create Draft: Creates a message draft. It does not send anything.
      </p>
      <InlineNotice tone="info">
        RelayWorks does not send emails automatically. It only creates drafts. Send manually,
        then click I Sent This Manually.
      </InlineNotice>
      {notice ? <InlineNotice tone="success">{notice}</InlineNotice> : null}
      {actionError ? <InlineNotice tone="error">{actionError}</InlineNotice> : null}
      {error ? <DataError message={error} /> : null}
      {!leads && loading ? <p className="text-sm text-muted">Loading leads...</p> : null}
      {leads && leads.length === 0 ? (
        <EmptyState
          title="No leads yet"
          description="Import a possible lead or add one manually to start creating drafts."
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
                <th className="px-3">Next step</th>
              </tr>
            </thead>
            <tbody>
              {sortedLeads.map((lead) => (
                <tr
                  key={lead.id}
                  id={`lead-row-${lead.id}`}
                  className={classNames(
                    "rounded-3xl text-sm text-foreground",
                    highlightedLeadId === lead.id ? "bg-emerald-50/95 ring-1 ring-emerald-300" : "bg-white/65",
                  )}
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
                          {lead.status === "contacted" ? "Already contacted" : "No draft action needed"}
                        </span>
                      )}
                      {highlightedLeadId === lead.id ? (
                        <p className="max-w-[18rem] text-xs font-medium leading-5 text-emerald-900">
                          Next: create a draft for this lead.
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
            : `${newLeadCount} new ${pluralize(newLeadCount, "lead")} can create drafts from the latest Sales Materials.`}
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
  copiedKey,
  highlighted,
  onCopy,
  onRefresh,
  onMarkSent,
}: {
  outreach: OutreachRecord[] | null;
  loading: boolean;
  error: string | null;
  busyOutreachId: string | null;
  copiedKey: string | null;
  highlighted?: boolean;
  onCopy: (copyKey: string, value: string) => void;
  onRefresh: () => void;
  onMarkSent: (outreachId: string) => void;
}) {
  const sorted = outreach ? sortNewestFirst(outreach) : [];

  return (
    <Card id="drafts-board" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Drafts"
        title="Messages"
        description="Review, copy, and manually send these drafts. RelayWorks never sends them for you."
        technicalLabel="Outreach records"
        action={<RefreshButton label="messages" onClick={onRefresh} disabled={loading} />}
      />
      <InlineNotice tone="warning">
        Only click I Sent This Manually after you copied and sent the message yourself.
      </InlineNotice>
      {error ? <DataError message={error} /> : null}
      {!outreach && loading ? <p className="text-sm text-muted">Loading message records...</p> : null}
      {outreach && outreach.length === 0 ? (
        <EmptyState
          title="No drafts yet"
          description="Create drafts from the Leads tab after you have Sales Materials and at least one lead."
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
                    <Badge label={`${items.length} ${pluralize(items.length, "message")}`} tone={getStatusTone(status)} />
                  </div>
                </div>
                <div className="mt-4 space-y-4">
                  {items.length === 0 ? (
                    <p className="text-sm text-muted">No {status} messages right now.</p>
                  ) : (
                    items.map((record) => (
                      <article key={record.id} className="rounded-3xl border border-border bg-card-strong p-4">
                        <div className="flex flex-col gap-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge label={humanize(record.status)} tone={getStatusTone(record.status)} />
                              <Badge label={record.channel} tone="bg-stone-200 text-stone-900" />
                            </div>
                            <CopyButton
                              copyKey={`outreach-${record.id}`}
                              copiedKey={copiedKey}
                              value={record.message}
                              onCopy={onCopy}
                            />
                          </div>
                          <div className="grid gap-3 md:grid-cols-2">
                            <InfoField label="Lead ID" value={record.lead_id} />
                            <InfoField label="Sales materials ID" value={record.asset_pack_id} />
                          </div>
                          <InfoField label="Created" value={formatDateTime(record.created_at)} />
                          <InfoField label="Message preview" value={previewMessage(record.message)} preserveWhitespace />
                          <details className="rounded-2xl border border-border bg-white/75 p-4">
                            <summary className="cursor-pointer text-sm font-semibold text-foreground">
                              Expand full message
                            </summary>
                            <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-foreground">
                              {record.message}
                            </p>
                          </details>
                          {record.status === "draft" ? (
                            <div className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4">
                              <p className="text-sm text-amber-950">
                                I Sent This Manually: Only click this after you manually sent this message yourself.
                              </p>
                              <button
                                type="button"
                                disabled={busyOutreachId === record.id}
                                onClick={() => onMarkSent(record.id)}
                                className="rounded-full bg-amber-900 px-4 py-2 text-sm font-semibold text-amber-50 transition hover:bg-amber-800 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                {busyOutreachId === record.id ? "Updating..." : "I Sent This Manually"}
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
  highlighted,
  onRefresh,
}: {
  followUps: FollowUpQueueItem[] | null;
  loading: boolean;
  error: string | null;
  highlighted?: boolean;
  onRefresh: () => void;
}) {
  return (
    <Card id="follow-up-queue" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Follow-ups"
        title="Follow-up Queue"
        description="These contacts had a sent message and may need a manual next step."
        action={<RefreshButton label="follow-ups" onClick={onRefresh} disabled={loading} />}
      />
      {error ? <DataError message={error} /> : null}
      {!followUps && loading ? <p className="text-sm text-muted">Loading follow-up queue...</p> : null}
      {followUps && followUps.length === 0 ? (
        <EmptyState
          title="No follow-ups due right now"
          description="Once a lead needs another manual touchpoint, it will show up here."
        />
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
                <InfoField label="Last message ID" value={item.last_outreach_id} />
              </div>
              <InfoField label="Last message" value={previewMessage(item.message)} preserveWhitespace />
              <InfoField
                label="Suggested next action"
                value="Review the last message, decide whether to send a short follow-up manually, and update the lead based on any reply."
              />
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
  copiedKey,
  highlighted,
  onCopy,
}: {
  assetPack: AssetPack | null;
  loading: boolean;
  error: string | null;
  copiedKey: string | null;
  highlighted?: boolean;
  onCopy: (copyKey: string, value: string) => void;
}) {
  return (
    <Card id="sales-materials" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Assets"
        title="Sales Materials"
        description="This is the latest pitch and message pack for the current project."
        technicalLabel="Asset pack"
      />
      {error ? <DataError message={error} /> : null}
      {!assetPack && loading ? <p className="text-sm text-muted">Loading Sales Materials...</p> : null}
      {!assetPack && !loading && !error ? (
        <EmptyState
          title="No Sales Materials yet"
          description="Create Sales Materials after you have a Business Plan."
        />
      ) : null}
      {assetPack ? (
        <div className="space-y-4">
          <InfoField label="Headline" value={assetPack.headline} secondaryValue={`Asset pack ID: ${assetPack.id}`} />
          <InfoField
            label="One-sentence pitch"
            value={assetPack.one_sentence_pitch}
            action={<CopyButton copyKey="asset-one-sentence-pitch" copiedKey={copiedKey} value={assetPack.one_sentence_pitch} onCopy={onCopy} />}
          />
          <InfoField
            label="Pilot offer"
            value={assetPack.pilot_offer}
            preserveWhitespace
            action={<CopyButton copyKey="asset-pilot-offer" copiedKey={copiedKey} value={assetPack.pilot_offer} onCopy={onCopy} />}
          />
          <InfoField
            label="Email subject"
            value={assetPack.cold_outreach_email_subject}
            action={<CopyButton copyKey="asset-email-subject" copiedKey={copiedKey} value={assetPack.cold_outreach_email_subject} onCopy={onCopy} />}
          />
          <InfoField
            label="Cold outreach draft message"
            value={assetPack.cold_outreach_email_body}
            preserveWhitespace
            action={<CopyButton copyKey="asset-email-body" copiedKey={copiedKey} value={assetPack.cold_outreach_email_body} onCopy={onCopy} />}
          />
          <InfoField
            label="LinkedIn DM"
            value={assetPack.linkedin_dm}
            preserveWhitespace
            action={<CopyButton copyKey="asset-linkedin-dm" copiedKey={copiedKey} value={assetPack.linkedin_dm} onCopy={onCopy} />}
          />
          <InfoField
            label="Discovery call script"
            value="Not available in the current asset pack."
            secondaryValue="If the backend adds this field later, it can appear here."
          />
        </div>
      ) : null}
    </Card>
  );
}

function LaunchPlanCard({
  launchPlan,
  loading,
  error,
  highlighted,
}: {
  launchPlan: LaunchPlan | null;
  loading: boolean;
  error: string | null;
  highlighted?: boolean;
}) {
  return (
    <Card id="business-plan" highlighted={highlighted} className="space-y-5">
      <SectionHeading
        eyebrow="Assets"
        title="Business Plan"
        description="This is the practical plan RelayWorks built from the current top opportunity."
        technicalLabel="Launch plan"
      />
      {error ? <DataError message={error} /> : null}
      {!launchPlan && loading ? <p className="text-sm text-muted">Loading Business Plan...</p> : null}
      {!launchPlan && !loading && !error ? (
        <EmptyState
          title="No Business Plan yet"
          description="Create a Business Plan after choosing a top opportunity."
        />
      ) : null}
      {launchPlan ? (
        <div className="space-y-4">
          <InfoField label="Headline" value={launchPlan.headline} secondaryValue={`Launch plan ID: ${launchPlan.id}`} />
          <InfoField label="Ideal customer profile" value={launchPlan.ideal_customer_profile} />
          <InfoField label="Offer summary" value={launchPlan.offer_summary} preserveWhitespace />
          <InfoField label="Pricing hypothesis" value={launchPlan.pricing_hypothesis} />
          <InfoField label="Sales motion" value={launchPlan.sales_motion} preserveWhitespace />
          <InfoField label="Launch recommendation" value={launchPlan.launch_recommendation} preserveWhitespace />
          <details className="rounded-3xl border border-border bg-white/60 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-foreground">
              Expand the full Business Plan
            </summary>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <InfoField label="Painful problem statement" value={launchPlan.painful_problem_statement} preserveWhitespace />
              <InfoField label="Selected opportunity" value={launchPlan.selected_opportunity.title} secondaryValue={launchPlan.selected_opportunity.offer} />
              <InfoField label="MVP scope" value={launchPlan.mvp_scope.join("\n")} preserveWhitespace />
              <InfoField label="Acquisition channels" value={launchPlan.acquisition_channels.join("\n")} preserveWhitespace />
              <InfoField label="First 30 day plan" value={launchPlan.first_30_day_plan.join("\n")} preserveWhitespace />
              <InfoField label="Success metrics" value={launchPlan.success_metrics.join("\n")} preserveWhitespace />
              <InfoField label="Biggest risks" value={launchPlan.biggest_risks.join("\n")} preserveWhitespace />
              <InfoField label="Mitigation steps" value={launchPlan.mitigation_steps.join("\n")} preserveWhitespace />
            </div>
          </details>
        </div>
      ) : null}
    </Card>
  );
}

function AdvancedDetailsCard({
  projectId,
  backendStatus,
  latestLaunchPlan,
  latestAssetPack,
  topOpportunity,
  candidateCount,
  leadCount,
  outreachCount,
  followUpCount,
}: {
  projectId: string;
  backendStatus: BackendStatusResponse | null;
  latestLaunchPlan: LaunchPlan | null;
  latestAssetPack: AssetPack | null;
  topOpportunity: OpportunityComparison["top_opportunity"];
  candidateCount: number;
  leadCount: number;
  outreachCount: number;
  followUpCount: number;
}) {
  return (
    <Card id="advanced-details" className="space-y-5">
      <SectionHeading
        eyebrow="Advanced"
        title="Technical Details"
        description="These are the raw IDs and implementation details that most beginners do not need first."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <InfoField label="Project ID" value={projectId} />
        <InfoField label="Backend URL" value={API_BASE_URL} />
        <InfoField label="Backend online" value={backendStatus?.online ? "true" : "false"} />
        <InfoField label="Top opportunity run ID" value={topOpportunity?.run_id ?? "No run yet"} />
        <InfoField label="Latest launch plan ID" value={latestLaunchPlan?.id ?? "No launch plan yet"} />
        <InfoField label="Latest asset pack ID" value={latestAssetPack?.id ?? "No asset pack yet"} />
        <InfoField label="Candidate lead count" value={String(candidateCount)} />
        <InfoField label="Lead count" value={String(leadCount)} />
        <InfoField label="Message count" value={String(outreachCount)} />
        <InfoField label="Follow-up count" value={String(followUpCount)} />
        <InfoField label="Launch plan source run ID" value={latestLaunchPlan?.source_run_id ?? "Unknown"} />
        <InfoField label="Asset pack launch plan ID" value={latestAssetPack?.launch_plan_id ?? "Unknown"} />
      </div>
    </Card>
  );
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

export function OperatorDashboard() {
  const backendStatus = useResource(getBackendStatus);
  const metrics = useResource(getPipelineMetrics);
  const candidates = useResource(getCandidateLeads);
  const leads = useResource(getLeads);
  const outreach = useResource(getOutreachRecords);
  const followUps = useResource(getFollowUpQueue);
  const assetPacks = useResource(getAssetPacks);
  const launchPlans = useResource(getLaunchPlans);

  const [activeTab, setActiveTab] = useState<DashboardTab>("home");
  const [highlightedSectionId, setHighlightedSectionId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
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
  const currentLaunchPlanMode = comparisonMode === "all" ? undefined : comparisonMode;

  const sortedCandidates = sortNewestFirst(candidates.data ?? []);
  const sortedLeads = sortNewestFirst(leads.data ?? []);
  const sortedOutreach = sortNewestFirst(outreach.data ?? []);
  const discoveredCandidates = sortedCandidates.filter((candidate) => candidate.status === "discovered");
  const newLeads = sortedLeads.filter((lead) => lead.status === "new");
  const draftRecords = sortedOutreach.filter((record) => record.status === "draft");
  const sentRecords = sortedOutreach.filter((record) => record.status === "sent");
  const followUpCount = followUps.data?.length ?? 0;
  const demoMode = PROJECT_ID === DEMO_PROJECT_ID;

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

  useEffect(() => {
    if (!highlightedSectionId) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setHighlightedSectionId(null);
    }, 2400);

    return () => window.clearTimeout(timeoutId);
  }, [highlightedSectionId]);

  useEffect(() => {
    if (!copiedKey) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setCopiedKey(null);
    }, 1600);

    return () => window.clearTimeout(timeoutId);
  }, [copiedKey]);

  function openTabAndSection(tab: DashboardTab, sectionId?: string) {
    setActiveTab(tab);
    if (!sectionId) {
      return;
    }

    setHighlightedSectionId(sectionId);
    window.setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
  }

  async function handleCopy(copyKey: string, value: string) {
    await navigator.clipboard.writeText(value);
    setCopiedKey(copyKey);
  }

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
        `Business ideas updated for ${humanize(run.mode)}. You can now create a Business Plan.`,
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
      setCandidateNotice(`Discovery completed. ${discovered.length} possible ${pluralize(discovered.length, "lead")} returned.`);
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
      setCandidateNotice("Lead imported. You can now create a message draft from the Leads tab.");
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
      setCandidateNotice("Possible lead rejected.");
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
      setGenerationError(comparisonError ?? "No top opportunity found yet. Find Business Ideas first.");
      setGenerationNotice(null);
      return;
    }

    setGeneratingLaunchPlan(true);
    setGenerationNotice(null);
    setGenerationError(null);

    try {
      const launchPlan = await generateLaunchPlan(currentLaunchPlanMode);
      setGenerationNotice(`Business Plan created from ${currentTopOpportunity.title}: ${launchPlan.headline}`);
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
      setAssetPackNotice(`Sales Materials created: ${assetPack.headline}`);
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

      setManualLeadNotice("Lead added. Next: create a message draft for this lead.");
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
      setLeadActionError("Create Sales Materials first.");
      setBusyLeadId(null);
      return;
    }

    try {
      const outreachDraft = await createOutreachDraft({
        leadId,
        assetPackId: latestAssetPack.id,
      });
      setLeadNotice(outreachDraft.deduped ? "A matching draft already existed for that lead." : "Draft created for the selected lead.");
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
      setLeadActionError("Create Sales Materials first.");
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
      setLeadNotice(`Draft batch complete. ${createdCount} created, ${dedupedCount} deduped.`);
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
      setOutreachNotice("Message marked as sent and lead status refreshed.");
      startTransition(() => {
        void Promise.all([outreach.refresh(), leads.refresh(), metrics.refresh(), followUps.refresh()]);
      });
    } catch (error) {
      setOutreachActionError(toErrorMessage(error));
    } finally {
      setBusyOutreachId(null);
    }
  }

  const backendResolved = Boolean(backendStatus.data || backendStatus.error || !backendStatus.loading);
  const backendOnline = backendStatus.data?.online ?? false;
  const coreLoading =
    comparisonLoading ||
    launchPlans.loading ||
    assetPacks.loading ||
    candidates.loading ||
    leads.loading ||
    outreach.loading ||
    followUps.loading;

  let nextStepRecommendation: NextStepRecommendation;

  if (!backendResolved) {
    nextStepRecommendation = {
      title: "Checking your setup",
      description: "The dashboard is still checking whether the backend is reachable.",
      ctaLabel: "Stay on Home",
      tab: "home",
    };
  } else if (!backendOnline) {
    nextStepRecommendation = {
      title: "Start the backend first.",
      description: "The frontend cannot load project actions until the local FastAPI server is running.",
      ctaLabel: "Refresh backend status",
      tab: "home",
      sectionId: "backend-status",
      refreshOnly: true,
    };
  } else if (!currentTopOpportunity && comparisonLoading) {
    nextStepRecommendation = {
      title: "Checking your current project state",
      description: "RelayWorks is still loading the latest opportunity comparison.",
      ctaLabel: "Open Opportunity Tab",
      tab: "opportunity",
      sectionId: "find-business-ideas",
    };
  } else if (!currentTopOpportunity) {
    nextStepRecommendation = {
      title: "Run Opportunity Analysis.",
      description: "You need a ranked business idea before you can create a Business Plan.",
      ctaLabel: "Go to Find Business Ideas",
      tab: "opportunity",
      sectionId: "find-business-ideas",
    };
  } else if (!latestLaunchPlan) {
    nextStepRecommendation = {
      title: "Generate a Launch Plan.",
      description: "Turn the top business idea into a practical Business Plan.",
      ctaLabel: "Go to Create Business Plan",
      tab: "opportunity",
      sectionId: "business-plan-generator",
    };
  } else if (!latestAssetPack) {
    nextStepRecommendation = {
      title: "Generate an Asset Pack.",
      description: "Create the pitch, email copy, LinkedIn message, and offer before drafting outreach.",
      ctaLabel: "Go to Create Sales Materials",
      tab: "assets",
      sectionId: "sales-materials-generator",
    };
  } else if ((candidates.data?.length ?? 0) === 0 && (leads.data?.length ?? 0) === 0 && !coreLoading) {
    nextStepRecommendation = {
      title: "Discover candidate leads or add a lead manually.",
      description: "You have Sales Materials, but no possible leads or imported leads yet.",
      ctaLabel: "Go to Leads",
      tab: "leads",
      sectionId: "lead-finder",
    };
  } else if (discoveredCandidates.length > 0) {
    nextStepRecommendation = {
      title: "Review candidate leads and import the good ones.",
      description: `${discoveredCandidates.length} possible ${pluralize(discoveredCandidates.length, "lead")} still need review.`,
      ctaLabel: "Review Possible Leads",
      tab: "leads",
      sectionId: "possible-leads",
    };
  } else if (newLeads.length > 0 && latestAssetPack) {
    nextStepRecommendation = {
      title: "Create outreach drafts for new leads.",
      description: `${newLeads.length} new ${pluralize(newLeads.length, "lead")} can be turned into message drafts now.`,
      ctaLabel: "Go to Leads",
      tab: "leads",
      sectionId: "leads-table",
    };
  } else if (draftRecords.length > 0) {
    nextStepRecommendation = {
      title: "Review drafts, manually send them, then click Mark as Sent.",
      description: `${draftRecords.length} draft ${pluralize(draftRecords.length, "message")} still need manual review.`,
      ctaLabel: "Go to Drafts",
      tab: "drafts",
      sectionId: "drafts-board",
    };
  } else if (sentRecords.length > 0 || followUpCount > 0) {
    nextStepRecommendation = {
      title: "Check follow-ups and update replies.",
      description: "You have sent outreach history, so the next operator job is checking for follow-up work.",
      ctaLabel: "Open Follow-ups",
      tab: "followups",
      sectionId: "follow-up-queue",
    };
  } else {
    nextStepRecommendation = {
      title: "Your workflow is up to date.",
      description: "Add more leads or run a new analysis when you want to work another batch.",
      ctaLabel: "Open Home",
      tab: "home",
    };
  }

  const workflowStates: WorkflowState[] = [
    currentTopOpportunity ? "done" : backendOnline ? "current" : "not_started",
    latestLaunchPlan ? "done" : currentTopOpportunity ? "current" : "not_started",
    latestAssetPack ? "done" : latestLaunchPlan ? "current" : "not_started",
    (sortedLeads.length > 0 || sortedCandidates.length > 0)
      ? "done"
      : latestAssetPack
        ? "current"
        : "not_started",
    sortedOutreach.length > 0 ? "done" : newLeads.length > 0 && latestAssetPack ? "current" : "not_started",
    sentRecords.length > 0 ? "done" : draftRecords.length > 0 ? "current" : "not_started",
    sentRecords.length > 0 ? "done" : draftRecords.length > 0 ? "not_started" : "not_started",
    followUpCount > 0 ? "current" : sentRecords.length > 0 ? "done" : "not_started",
  ];

  return (
    <main className="min-h-screen px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-6">
        <Card className="overflow-hidden p-0">
          <div className="border-b border-white/50 bg-[linear-gradient(135deg,rgba(31,106,82,0.92),rgba(16,42,35,0.9)_58%,rgba(154,95,17,0.72))] px-6 py-8 text-stone-50 sm:px-8">
            <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
              <div className="max-w-4xl space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge label="RelayWorks Operator Dashboard" tone="bg-white/16 text-white" />
                  <Badge label="Beginner-friendly workflow" tone="bg-black/18 text-white" />
                </div>
                <div className="space-y-3">
                  <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
                    Run the workflow without thinking in API terms.
                  </h1>
                  <p className="max-w-3xl text-base leading-7 text-stone-100/92 sm:text-lg">
                    Use the Home tab to understand what RelayWorks does, what is ready now, and
                    which operator step should happen next.
                  </p>
                </div>
              </div>
              <div className="rounded-[28px] border border-white/14 bg-black/14 px-5 py-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-stone-200">
                  Current Project
                </p>
                <p className="mt-2 break-all text-sm font-semibold text-white">{PROJECT_ID}</p>
                <p className="mt-2 text-sm text-stone-200">Backend: {API_BASE_URL}</p>
              </div>
            </div>
          </div>
          <div className="bg-white/35 px-6 py-5 sm:px-8">
            <div className="flex flex-wrap gap-2">
              {DASHBOARD_TABS.map((tab) => (
                <TabButton
                  key={tab.id}
                  active={activeTab === tab.id}
                  label={tab.label}
                  onClick={() => setActiveTab(tab.id)}
                />
              ))}
            </div>
          </div>
        </Card>

        {activeTab === "home" ? (
          <div className="space-y-6">
            <section className="section-grid grid gap-6 xl:grid-cols-[1.05fr_1fr]">
              <HomeStartHereCard demoMode={demoMode} />
              <NextStepCard
                recommendation={nextStepRecommendation}
                onOpen={openTabAndSection}
                onRefreshBackend={() => {
                  void backendStatus.refresh();
                }}
              />
            </section>

            <WorkflowChecklist states={workflowStates} />

            <section className="section-grid grid gap-6 xl:grid-cols-[1fr_1fr_1.1fr]">
              <StatusCard
                status={backendStatus.data}
                loading={backendStatus.loading}
                error={backendStatus.error}
                highlighted={highlightedSectionId === "backend-status"}
              />
              <HomeMetricsCard
                candidateCount={discoveredCandidates.length}
                leadCount={sortedLeads.length}
                draftCount={draftRecords.length}
                followUpCount={followUpCount}
              />
              <HomeOpportunityCard
                topOpportunity={currentTopOpportunity}
                loading={comparisonLoading}
                error={comparisonError}
                onOpenOpportunity={() => openTabAndSection("opportunity")}
              />
            </section>
          </div>
        ) : null}

        {activeTab === "opportunity" ? (
          <div className="space-y-6">
            <section className="section-grid grid gap-6 xl:grid-cols-2">
              <OpportunityAnalysisCard
                objective={analysisObjective}
                mode={analysisMode}
                numOpportunities={analysisNumOpportunities}
                loading={runningAnalysis}
                notice={analysisNotice}
                error={analysisError}
                highlighted={highlightedSectionId === "find-business-ideas"}
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

            <ActionCard
              id="business-plan-generator"
              highlighted={highlightedSectionId === "business-plan-generator"}
              eyebrow="Opportunity"
              title="Create Business Plan"
              description="Turn the current top opportunity into a practical plan."
              technicalLabel="Launch plan generation"
              helperText="Create Business Plan: Turns the best idea into a practical plan."
              buttonLabel="Create Business Plan"
              loadingLabel="Creating Business Plan..."
              loading={generatingLaunchPlan}
              disabled={!comparisonError && (comparisonLoading || !currentTopOpportunity)}
              notice={generationNotice}
              error={generationError}
              onClick={handleGenerateLaunchPlan}
            >
              {currentTopOpportunity ? (
                <InfoField
                  label="Current source"
                  value={currentTopOpportunity.title}
                  secondaryValue={`${humanize(currentTopOpportunity.mode)} · Run ${currentTopOpportunity.run_id}`}
                />
              ) : (
                <InlineNotice tone="warning">
                  No top opportunity found yet. Find Business Ideas first.
                </InlineNotice>
              )}
            </ActionCard>
          </div>
        ) : null}

        {activeTab === "leads" ? (
          <div className="space-y-6">
            <Card id="lead-finder" highlighted={highlightedSectionId === "lead-finder"} className="space-y-6">
              <SectionHeading
                eyebrow="Leads"
                title="Lead Finder"
                description="Discover possible leads, review them, or add a known lead yourself."
              />
              {candidateNotice ? <InlineNotice tone="success">{candidateNotice}</InlineNotice> : null}
              {candidateActionError ? <InlineNotice tone="error">{candidateActionError}</InlineNotice> : null}
              {candidates.error ? <DataError message={candidates.error} /> : null}
              <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
                <form onSubmit={handleDiscoverCandidates} className="rounded-[28px] border border-border bg-white/60 p-5">
                  <div className="space-y-4">
                    <div>
                      <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
                        Discovery
                      </p>
                      <h3 className="mt-2 text-xl font-semibold text-foreground">
                        Discover Possible Leads
                      </h3>
                      <p className="mt-2 text-sm leading-6 text-muted">
                        Suggests companies that might fit. Emails are not verified.
                      </p>
                    </div>
                    <InlineNotice tone="warning">
                      These are suggestions only. Review each one before importing it.
                    </InlineNotice>
                    <label className="block space-y-2">
                      <span className="text-sm font-semibold text-foreground">Who should RelayWorks look for?</span>
                      <textarea
                        value={target}
                        onChange={(event) => setTarget(event.target.value)}
                        rows={7}
                        className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm leading-6 text-foreground outline-none ring-0 transition focus:border-emerald-500"
                      />
                    </label>
                    <label className="block space-y-2">
                      <span className="text-sm font-semibold text-foreground">How many?</span>
                      <input
                        type="number"
                        min={1}
                        max={25}
                        value={count}
                        onChange={(event) => setCount(Math.min(25, Math.max(1, Number(event.target.value) || 1)))}
                        className="w-full rounded-3xl border border-border bg-white px-4 py-3 text-sm text-foreground outline-none ring-0 transition focus:border-emerald-500"
                      />
                    </label>
                    <PrimaryButton
                      type="submit"
                      label="Discover Possible Leads"
                      loadingLabel="Discovering..."
                      loading={discovering}
                      fullWidth
                    />
                  </div>
                </form>

                <div id="possible-leads" className="space-y-4 scroll-mt-28">
                  {!candidates.data && candidates.loading ? (
                    <p className="text-sm text-muted">Loading possible leads...</p>
                  ) : null}
                  {candidates.data && candidates.data.length === 0 ? (
                    <EmptyState
                      title="No possible leads yet"
                      description="Run lead discovery or add a lead manually to get started."
                    />
                  ) : null}
                  {candidates.data && candidates.data.length > 0
                    ? sortedCandidates.map((candidate) => (
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
                highlighted={highlightedSectionId === "manual-lead"}
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
                highlighted={highlightedSectionId === "leads-table"}
                onRefresh={leads.refresh}
                onCreateDraft={handleCreateDraft}
                onCreateDraftsForNewLeads={handleCreateDraftsForNewLeads}
              />
            </section>
          </div>
        ) : null}

        {activeTab === "drafts" ? (
          <div className="space-y-4">
            {outreachNotice ? <InlineNotice tone="success">{outreachNotice}</InlineNotice> : null}
            {outreachActionError ? <InlineNotice tone="error">{outreachActionError}</InlineNotice> : null}
            <OutreachBoard
              outreach={outreach.data}
              loading={outreach.loading}
              error={outreach.error}
              busyOutreachId={busyOutreachId}
              copiedKey={copiedKey}
              highlighted={highlightedSectionId === "drafts-board"}
              onCopy={(copyKey, value) => {
                void handleCopy(copyKey, value);
              }}
              onRefresh={outreach.refresh}
              onMarkSent={handleMarkSent}
            />
          </div>
        ) : null}

        {activeTab === "followups" ? (
          <FollowUpSection
            followUps={followUps.data}
            loading={followUps.loading}
            error={followUps.error}
            highlighted={highlightedSectionId === "follow-up-queue"}
            onRefresh={followUps.refresh}
          />
        ) : null}

        {activeTab === "assets" ? (
          <div className="space-y-6">
            <ActionCard
              id="sales-materials-generator"
              highlighted={highlightedSectionId === "sales-materials-generator"}
              eyebrow="Assets"
              title="Create Sales Materials"
              description="Create the latest message and offer pack from the current Business Plan."
              technicalLabel="Asset pack generation"
              helperText="Create Sales Materials: Creates your pitch, email copy, LinkedIn message, and pilot offer."
              buttonLabel="Create Sales Materials"
              loadingLabel="Creating Sales Materials..."
              loading={generatingAssetPack}
              notice={assetPackNotice}
              error={assetPackError}
              onClick={handleGenerateAssetPack}
            />

            <section className="section-grid grid gap-6 xl:grid-cols-2">
              <LaunchPlanCard
                launchPlan={latestLaunchPlan}
                loading={launchPlans.loading}
                error={launchPlans.error}
                highlighted={highlightedSectionId === "business-plan"}
              />
              <AssetPackCard
                assetPack={latestAssetPack}
                loading={assetPacks.loading}
                error={assetPacks.error}
                copiedKey={copiedKey}
                highlighted={highlightedSectionId === "sales-materials"}
                onCopy={(copyKey, value) => {
                  void handleCopy(copyKey, value);
                }}
              />
            </section>
          </div>
        ) : null}

        {activeTab === "metrics" ? (
          <MetricsCard
            metrics={metrics.data}
            loading={metrics.loading}
            error={metrics.error}
            onRefresh={metrics.refresh}
          />
        ) : null}

        {activeTab === "advanced" ? (
          <AdvancedDetailsCard
            projectId={PROJECT_ID}
            backendStatus={backendStatus.data}
            latestLaunchPlan={latestLaunchPlan}
            latestAssetPack={latestAssetPack}
            topOpportunity={currentTopOpportunity}
            candidateCount={sortedCandidates.length}
            leadCount={sortedLeads.length}
            outreachCount={sortedOutreach.length}
            followUpCount={followUpCount}
          />
        ) : null}
      </div>
    </main>
  );
}
