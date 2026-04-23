from typing import Literal

from pydantic import BaseModel

LeadStatus = Literal["new", "contacted", "replied", "interested", "closed"]


class LeadCreate(BaseModel):
    project_id: str
    company_name: str
    contact_name: str
    contact_email: str
    status: LeadStatus = "new"


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadResponse(BaseModel):
    id: str
    project_id: str
    company_name: str
    contact_name: str
    contact_email: str
    status: LeadStatus
    created_at: str
