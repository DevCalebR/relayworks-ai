from typing import Literal

from pydantic import BaseModel

LeadStatus = Literal["new", "contacted", "replied", "interested", "closed"]


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
