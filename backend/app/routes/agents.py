from fastapi import APIRouter, HTTPException

from app.schemas.run import CompareResponse, OperatorMode, RunRequest, RunResponse
from app.services.memory_service import compare_best_runs, get_project, list_runs
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
        mode=run_request.mode,
        num_opportunities=run_request.num_opportunities,
    )
    return RunResponse(**result)


@router.get("/runs", response_model=list[RunResponse])
def list_runs_endpoint(project_id: str | None = None) -> list[RunResponse]:
    return [RunResponse(**run) for run in list_runs(project_id=project_id)]


@router.get("/compare", response_model=CompareResponse)
def compare_runs_endpoint(project_id: str, mode: OperatorMode | None = None) -> CompareResponse:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return CompareResponse(**compare_best_runs(project_id=project_id, mode=mode))
