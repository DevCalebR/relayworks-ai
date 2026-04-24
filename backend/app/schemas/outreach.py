from typing import Literal

from pydantic import BaseModel

from app.schemas.lead import LeadResponse

OutreachChannel = Literal["email", "linkedin", "other"]
OutreachStatus = Literal["draft", "sent", "replied", "ignored"]


class OutreachRequest(BaseModel):
    project_id: str
    lead_id: str
    asset_pack_id: str
    channel: OutreachChannel = "email"
    dedupe: bool = True


class OutreachBatchRequest(BaseModel):
    project_id: str
    lead_ids: list[str]
    asset_pack_id: str
    channel: OutreachChannel = "email"
    dedupe: bool = True


class OutreachStatusUpdate(BaseModel):
    status: OutreachStatus
    reply_text: str | None = None


class OutreachMarkSentRequest(BaseModel):
    mark_lead_contacted: bool = False


class OutreachLogResponse(BaseModel):
    id: str
    project_id: str
    lead_id: str
    asset_pack_id: str
    channel: OutreachChannel
    message: str
    status: OutreachStatus
    reply_text: str | None = None
    created_at: str
    deduped: bool = False


class OutreachMarkSentResponse(BaseModel):
    outreach: OutreachLogResponse
    lead: LeadResponse | None = None
