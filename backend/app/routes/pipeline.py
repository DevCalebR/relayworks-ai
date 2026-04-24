from fastapi import APIRouter, HTTPException

from app.schemas.outreach import OutreachLogResponse
from app.schemas.pipeline import FollowUpQueueItem, FollowUpRequest, PipelineMetricsResponse
from app.services.personalization_agent import generate_personalized_follow_up
from app.services.memory_service import (
    create_outreach_log,
    get_asset_pack_record,
    get_latest_outreach_record,
    get_lead_record,
    get_pipeline_metrics,
    get_project,
    list_follow_up_queue,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/metrics", response_model=PipelineMetricsResponse)
def get_pipeline_metrics_endpoint(project_id: str) -> PipelineMetricsResponse:
    return PipelineMetricsResponse(**get_pipeline_metrics(project_id=project_id))


@router.get("/follow-ups", response_model=list[FollowUpQueueItem])
def get_follow_up_queue_endpoint(project_id: str) -> list[FollowUpQueueItem]:
    return [FollowUpQueueItem(**item) for item in list_follow_up_queue(project_id=project_id)]


@router.post("/follow-ups/{lead_id}", response_model=OutreachLogResponse)
def create_follow_up_endpoint(
    lead_id: str,
    request: FollowUpRequest,
) -> OutreachLogResponse:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    lead = get_lead_record(lead_id=lead_id, project_id=request.project_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found for project")

    latest_outreach = get_latest_outreach_record(project_id=request.project_id, lead_id=lead_id)
    if latest_outreach is None:
        raise HTTPException(status_code=404, detail="No outreach found for lead")

    asset_pack = get_asset_pack_record(
        asset_pack_id=str(latest_outreach.get("asset_pack_id") or ""),
        project_id=request.project_id,
    )
    follow_up_message, _generation_mode = generate_personalized_follow_up(
        lead=lead,
        latest_outreach=latest_outreach,
        channel=request.channel,
        asset_pack=asset_pack,
    )
    outreach_log = create_outreach_log(
        {
            "project_id": request.project_id,
            "lead_id": lead_id,
            "asset_pack_id": str(latest_outreach.get("asset_pack_id") or ""),
            "channel": request.channel,
            "message": follow_up_message,
            "status": "sent",
        }
    )
    return OutreachLogResponse(**outreach_log)
