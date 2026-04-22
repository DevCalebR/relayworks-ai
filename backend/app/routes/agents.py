from fastapi import APIRouter, HTTPException

from app.schemas.run import RunRequest, RunResponse
from app.services.memory_service import get_project
from app.services.orchestrator import run_agents

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run", response_model=RunResponse)
def run_agents_endpoint(run_request: RunRequest) -> RunResponse:
    project = get_project(run_request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = run_agents(
        project_id=run_request.project_id,
        objective=run_request.objective,
    )
    return RunResponse(**result)
