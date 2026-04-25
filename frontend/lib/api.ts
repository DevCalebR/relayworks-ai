export const PROJECT_ID = "proj_952a38d1f320";
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type RequestOptions = RequestInit & {
  path: string;
};

export type CandidateStatus = "discovered" | "imported" | "rejected";
export type LeadStatus = "new" | "contacted" | "replied" | "interested" | "closed";
export type OutreachStatus = "draft" | "sent" | "replied" | "ignored";
export type OutreachChannel = "email" | "linkedin" | "other";

export interface BackendRootResponse {
  message: string;
}

export interface BackendHealthResponse {
  status: string;
}

export interface BackendStatusResponse {
  root: BackendRootResponse;
  health: BackendHealthResponse;
  online: boolean;
}

export interface PipelineMetrics {
  project_id: string;
  lead_counts: {
    new: number;
    contacted: number;
    replied: number;
    interested: number;
    closed: number;
    total: number;
  };
  outreach_counts: {
    draft: number;
    sent: number;
    replied: number;
    ignored: number;
    total: number;
  };
}

export interface CandidateLead {
  id: string;
  project_id: string;
  company_name: string;
  contact_name: string | null;
  contact_title: string | null;
  contact_email: string | null;
  company_description: string | null;
  industry: string | null;
  website: string | null;
  linkedin_url: string | null;
  lead_source: string | null;
  fit_reason: string;
  confidence_score: number;
  status: CandidateStatus;
  created_at: string;
}

export interface Lead {
  id: string;
  project_id: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  status: LeadStatus;
  company_description: string | null;
  industry: string | null;
  website: string | null;
  notes: string | null;
  created_at: string;
  deduped: boolean;
}

export interface OutreachRecord {
  id: string;
  project_id: string;
  lead_id: string;
  asset_pack_id: string;
  channel: OutreachChannel;
  message: string;
  status: OutreachStatus;
  reply_text: string | null;
  created_at: string;
  deduped: boolean;
}

export interface FollowUpQueueItem {
  lead_id: string;
  company_name: string;
  contact_name: string;
  last_outreach_id: string;
  channel: OutreachChannel;
  message: string;
}

export interface AssetPack {
  id: string;
  project_id: string;
  launch_plan_id: string;
  source_run_id: string;
  headline: string;
  one_sentence_pitch: string;
  pilot_offer: string;
  cold_outreach_email_subject: string;
  cold_outreach_email_body: string;
  linkedin_dm: string;
  created_at: string;
}

export interface LaunchPlan {
  id: string;
  project_id: string;
  source_run_id: string;
  headline: string;
  ideal_customer_profile: string;
  offer_summary: string;
  pricing_hypothesis: string;
  sales_motion: string;
  launch_recommendation: string;
  created_at: string;
}

interface CandidateImportResponse {
  candidate_lead: CandidateLead;
  lead: Lead;
}

interface OutreachMarkSentResponse {
  outreach: OutreachRecord;
  lead: Lead | null;
}

interface CandidateDiscoveryRequest {
  target: string;
  count: number;
}

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function requestJson<T>({ path, headers, ...init }: RequestOptions): Promise<T> {
  const requestHeaders = new Headers(headers);
  const hasBody = init.body !== undefined;
  if (hasBody && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(buildUrl(path), {
      ...init,
      cache: "no-store",
      headers: requestHeaders,
    });
    const payloadText = await response.text();
    const payload = payloadText ? JSON.parse(payloadText) : null;

    if (!response.ok) {
      const detail =
        (payload && typeof payload === "object" && "detail" in payload && payload.detail) ||
        (payload && typeof payload === "object" && "message" in payload && payload.message) ||
        `Request failed with status ${response.status}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    return payload as T;
  } catch (error) {
    if (error instanceof Error && error.message.toLowerCase().includes("failed to fetch")) {
      throw new Error(
        `Could not reach the backend at ${API_BASE_URL}. Make sure the FastAPI server is running.`,
      );
    }
    throw error;
  }
}

function withProjectId(path: string): string {
  const joiner = path.includes("?") ? "&" : "?";
  return `${path}${joiner}project_id=${encodeURIComponent(PROJECT_ID)}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Unknown";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatWebsite(website: string | null | undefined): string {
  if (!website) {
    return "No website listed";
  }
  return website.replace(/^https?:\/\//, "");
}

export function previewMessage(message: string, maxLength = 160): string {
  if (message.length <= maxLength) {
    return message;
  }
  return `${message.slice(0, maxLength).trimEnd()}...`;
}

export function getLatestRecord<T extends { created_at: string }>(records: T[]): T | null {
  if (records.length === 0) {
    return null;
  }

  return [...records].sort((left, right) =>
    right.created_at.localeCompare(left.created_at),
  )[0] ?? null;
}

export function sortNewestFirst<T extends { created_at: string }>(records: T[]): T[] {
  return [...records].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

export async function getBackendStatus(): Promise<BackendStatusResponse> {
  const [root, health] = await Promise.all([
    requestJson<BackendRootResponse>({ path: "/" }),
    requestJson<BackendHealthResponse>({ path: "/health" }),
  ]);

  return {
    root,
    health,
    online: health.status === "ok",
  };
}

export async function getPipelineMetrics(): Promise<PipelineMetrics> {
  return requestJson<PipelineMetrics>({
    path: withProjectId("/pipeline/metrics"),
  });
}

export async function getCandidateLeads(): Promise<CandidateLead[]> {
  return requestJson<CandidateLead[]>({
    path: withProjectId("/leads/candidates"),
  });
}

export async function discoverCandidateLeads(
  payload: CandidateDiscoveryRequest,
): Promise<CandidateLead[]> {
  return requestJson<CandidateLead[]>({
    path: "/leads/discover",
    method: "POST",
    body: JSON.stringify({
      project_id: PROJECT_ID,
      target: payload.target,
      count: payload.count,
    }),
  });
}

export async function importCandidateLead(candidateLeadId: string): Promise<CandidateImportResponse> {
  return requestJson<CandidateImportResponse>({
    path: `/leads/candidates/${candidateLeadId}/import`,
    method: "POST",
  });
}

export async function rejectCandidateLead(candidateLeadId: string): Promise<CandidateLead> {
  return requestJson<CandidateLead>({
    path: `/leads/candidates/${candidateLeadId}/reject`,
    method: "POST",
  });
}

export async function getLeads(): Promise<Lead[]> {
  return requestJson<Lead[]>({
    path: withProjectId("/leads"),
  });
}

export async function getOutreachRecords(): Promise<OutreachRecord[]> {
  return requestJson<OutreachRecord[]>({
    path: withProjectId("/agents/outreach"),
  });
}

export async function markOutreachSent(outreachId: string): Promise<OutreachMarkSentResponse> {
  return requestJson<OutreachMarkSentResponse>({
    path: `/agents/outreach/${outreachId}/mark-sent`,
    method: "POST",
    body: JSON.stringify({
      mark_lead_contacted: true,
    }),
  });
}

export async function getFollowUpQueue(): Promise<FollowUpQueueItem[]> {
  return requestJson<FollowUpQueueItem[]>({
    path: withProjectId("/pipeline/follow-ups"),
  });
}

export async function getAssetPacks(): Promise<AssetPack[]> {
  return requestJson<AssetPack[]>({
    path: withProjectId("/agents/asset-packs"),
  });
}

export async function getLaunchPlans(): Promise<LaunchPlan[]> {
  return requestJson<LaunchPlan[]>({
    path: withProjectId("/agents/launch-plans"),
  });
}
