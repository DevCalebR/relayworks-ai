from typing import Literal

from pydantic import BaseModel, Field

LeadStatus = Literal["new", "contacted", "replied", "interested", "closed"]
CandidateLeadStatus = Literal["discovered", "imported", "rejected"]


class LeadCreate(BaseModel):
    project_id: str
    company_name: str
    contact_name: str
    contact_email: str
    dedupe: bool = True
    status: LeadStatus = "new"
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


class LeadBatchItem(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    status: LeadStatus = "new"
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


class LeadBatchCreate(BaseModel):
    project_id: str
    dedupe: bool = True
    leads: list[LeadBatchItem]


class LeadStatusUpdate(BaseModel):
    status: LeadStatus | None = None
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


class LeadResponse(BaseModel):
    id: str
    project_id: str
    company_name: str
    contact_name: str
    contact_email: str
    status: LeadStatus
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None
    created_at: str
    deduped: bool = False


class LeadActivityOutreachItem(BaseModel):
    id: str
    status: str
    channel: str
    asset_pack_id: str
    message: str
    reply_text: str | None = None
    created_at: str


class LeadActivityResponse(BaseModel):
    lead: LeadResponse
    outreach: list[LeadActivityOutreachItem]


class CandidateLeadResponse(BaseModel):
    id: str
    project_id: str
    company_name: str
    contact_name: str | None = None
    contact_title: str | None = None
    contact_email: str | None = None
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    lead_source: str | None = None
    fit_reason: str
    confidence_score: int = Field(ge=1, le=10)
    status: CandidateLeadStatus
    created_at: str


class CandidateLeadDiscoverRequest(BaseModel):
    project_id: str
    target: str
    count: int = Field(default=10, ge=1, le=25)
    mode: str = "manual_research"


class CandidateLeadImportResponse(BaseModel):
    candidate_lead: CandidateLeadResponse
    lead: LeadResponse
