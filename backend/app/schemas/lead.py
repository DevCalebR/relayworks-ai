from typing import Literal

from pydantic import BaseModel

LeadStatus = Literal["new", "contacted", "replied", "interested", "closed"]


class LeadCreate(BaseModel):
    project_id: str
    company_name: str
    contact_name: str
    contact_email: str
    status: LeadStatus = "new"
    company_description: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


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
