from fastapi import APIRouter, HTTPException

from app.schemas.launch_plan import LaunchPlanRequest, LaunchPlanResponse
from app.schemas.run import CompareResponse, OperatorMode, RunRequest, RunResponse
from app.services.launch_plan_agent import generate_launch_plan
from app.services.memory_service import (
    compare_best_runs,
    create_launch_plan_record,
    get_project,
    list_launch_plans,
    list_runs,
    resolve_launch_plan_source,
)
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


@router.post("/launch-plan", response_model=LaunchPlanResponse)
def launch_plan_endpoint(request: LaunchPlanRequest) -> LaunchPlanResponse:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    source = resolve_launch_plan_source(
        project_id=request.project_id,
        run_id=request.run_id,
        mode=request.mode,
        use_top_opportunity=request.use_top_opportunity,
    )
    if source is None:
        if request.run_id is None and not request.use_top_opportunity:
            raise HTTPException(
                status_code=400,
                detail="Provide run_id or set use_top_opportunity=true.",
            )
        raise HTTPException(status_code=404, detail="Could not resolve a launch-plan source.")

    launch_plan, generation_mode = generate_launch_plan(
        project_id=request.project_id,
        source_run_id=source["source_run_id"],
        mode=source["mode"],
        selected_opportunity=source["selected_opportunity"],
        objective=source["objective"],
    )
    saved_launch_plan = create_launch_plan_record(
        {**launch_plan, "generation_mode": generation_mode}
    )
    return LaunchPlanResponse(**saved_launch_plan)


@router.get("/launch-plans", response_model=list[LaunchPlanResponse])
def list_launch_plans_endpoint(
    project_id: str | None = None,
    run_id: str | None = None,
) -> list[LaunchPlanResponse]:
    return [
        LaunchPlanResponse(**launch_plan)
        for launch_plan in list_launch_plans(project_id=project_id, run_id=run_id)
    ]
