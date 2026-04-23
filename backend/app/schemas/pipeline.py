from pydantic import BaseModel


class LeadCounts(BaseModel):
    new: int
    contacted: int
    replied: int
    interested: int
    closed: int
    total: int


class OutreachCounts(BaseModel):
    sent: int
    replied: int
    ignored: int
    total: int


class PipelineMetricsResponse(BaseModel):
    project_id: str
    lead_counts: LeadCounts
    outreach_counts: OutreachCounts


class FollowUpQueueItem(BaseModel):
    lead_id: str
    company_name: str
    contact_name: str
    last_outreach_id: str
    channel: str
    message: str
