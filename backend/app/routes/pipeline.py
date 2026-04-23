from fastapi import APIRouter

from app.schemas.pipeline import PipelineMetricsResponse
from app.services.memory_service import get_pipeline_metrics

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/metrics", response_model=PipelineMetricsResponse)
def get_pipeline_metrics_endpoint(project_id: str) -> PipelineMetricsResponse:
    return PipelineMetricsResponse(**get_pipeline_metrics(project_id=project_id))
