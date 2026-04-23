from typing import Literal

from pydantic import BaseModel

OutreachChannel = Literal["email", "linkedin", "other"]
OutreachStatus = Literal["sent", "replied", "ignored"]


class OutreachRequest(BaseModel):
    project_id: str
    lead_id: str
    asset_pack_id: str
    channel: OutreachChannel = "email"


class OutreachBatchRequest(BaseModel):
    project_id: str
    lead_ids: list[str]
    asset_pack_id: str
    channel: OutreachChannel = "email"


class OutreachStatusUpdate(BaseModel):
    status: OutreachStatus


class OutreachLogResponse(BaseModel):
    id: str
    project_id: str
    lead_id: str
    asset_pack_id: str
    channel: OutreachChannel
    message: str
    status: OutreachStatus
    created_at: str
