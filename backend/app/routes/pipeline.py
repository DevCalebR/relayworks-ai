from fastapi import APIRouter

from app.schemas.pipeline import FollowUpQueueItem, PipelineMetricsResponse
from app.services.memory_service import get_pipeline_metrics, list_follow_up_queue

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/metrics", response_model=PipelineMetricsResponse)
def get_pipeline_metrics_endpoint(project_id: str) -> PipelineMetricsResponse:
    return PipelineMetricsResponse(**get_pipeline_metrics(project_id=project_id))


@router.get("/follow-ups", response_model=list[FollowUpQueueItem])
def get_follow_up_queue_endpoint(project_id: str) -> list[FollowUpQueueItem]:
    return [FollowUpQueueItem(**item) for item in list_follow_up_queue(project_id=project_id)]
