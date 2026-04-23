from fastapi import APIRouter, HTTPException

from app.schemas.asset_pack import AssetPackRequest, AssetPackResponse
from app.schemas.launch_plan import LaunchPlanRequest, LaunchPlanResponse
from app.schemas.outreach import (
    OutreachBatchRequest,
    OutreachLogResponse,
    OutreachRequest,
    OutreachStatusUpdate,
)
from app.schemas.run import CompareResponse, OperatorMode, RunRequest, RunResponse
from app.services.asset_pack_agent import generate_asset_pack
from app.services.launch_plan_agent import generate_launch_plan
from app.services.memory_service import (
    compare_best_runs,
    create_asset_pack_record,
    create_launch_plan_record,
    create_outreach_log,
    get_asset_pack_record,
    get_lead_record,
    get_project,
    get_outreach_log_record,
    list_asset_packs,
    list_launch_plans,
    list_outreach_logs,
    list_runs,
    resolve_launch_plan_source,
    resolve_stored_launch_plan,
    update_outreach_status,
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


@router.post("/asset-pack", response_model=AssetPackResponse)
def asset_pack_endpoint(request: AssetPackRequest) -> AssetPackResponse:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    launch_plan = resolve_stored_launch_plan(
        project_id=request.project_id,
        launch_plan_id=request.launch_plan_id,
        use_latest_launch_plan=request.use_latest_launch_plan,
    )
    if launch_plan is None:
        if request.launch_plan_id is None and not request.use_latest_launch_plan:
            raise HTTPException(
                status_code=400,
                detail="Provide launch_plan_id or set use_latest_launch_plan=true.",
            )
        if request.launch_plan_id is not None:
            raise HTTPException(status_code=404, detail="Launch plan not found for project.")
        raise HTTPException(status_code=404, detail="No launch plan found for project.")

    asset_pack, generation_mode = generate_asset_pack(launch_plan=launch_plan)
    saved_asset_pack = create_asset_pack_record(
        {**asset_pack, "generation_mode": generation_mode}
    )
    return AssetPackResponse(**saved_asset_pack)


@router.get("/asset-packs", response_model=list[AssetPackResponse])
def list_asset_packs_endpoint(
    project_id: str | None = None,
    launch_plan_id: str | None = None,
) -> list[AssetPackResponse]:
    return [
        AssetPackResponse(**asset_pack)
        for asset_pack in list_asset_packs(
            project_id=project_id,
            launch_plan_id=launch_plan_id,
        )
    ]


def _resolve_outreach_message(asset_pack: dict, channel: str) -> str:
    email_subject = str(asset_pack.get("cold_outreach_email_subject") or "").strip()
    email_body = str(asset_pack.get("cold_outreach_email_body") or "").strip()
    linkedin_dm = str(asset_pack.get("linkedin_dm") or "").strip()

    if channel == "linkedin":
        return linkedin_dm
    if channel == "email":
        if email_subject and email_body:
            return f"Subject: {email_subject}\n\n{email_body}"
        return email_body
    return linkedin_dm or (
        f"Subject: {email_subject}\n\n{email_body}" if email_subject and email_body else email_body
    )


def _resolve_project_outreach_message(
    project_id: str,
    asset_pack_id: str,
    channel: str,
) -> str:
    asset_pack = get_asset_pack_record(
        asset_pack_id=asset_pack_id,
        project_id=project_id,
    )
    if asset_pack is None:
        raise HTTPException(status_code=404, detail="Asset pack not found for project")

    message = _resolve_outreach_message(asset_pack=asset_pack, channel=channel)
    if not message:
        raise HTTPException(status_code=400, detail="Asset pack does not contain outreach copy")
    return message


def _create_outreach_record(
    project_id: str,
    lead_id: str,
    asset_pack_id: str,
    channel: str,
) -> dict:
    lead = get_lead_record(lead_id=lead_id, project_id=project_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead not found for project: {lead_id}")

    message = _resolve_project_outreach_message(
        project_id=project_id,
        asset_pack_id=asset_pack_id,
        channel=channel,
    )
    return create_outreach_log(
        {
            "project_id": project_id,
            "lead_id": lead_id,
            "asset_pack_id": asset_pack_id,
            "channel": channel,
            "message": message,
            "status": "sent",
        }
    )


@router.post("/outreach", response_model=OutreachLogResponse)
def create_outreach_endpoint(request: OutreachRequest) -> OutreachLogResponse:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    outreach_log = _create_outreach_record(
        project_id=request.project_id,
        lead_id=request.lead_id,
        asset_pack_id=request.asset_pack_id,
        channel=request.channel,
    )
    return OutreachLogResponse(**outreach_log)


@router.post("/outreach/batch", response_model=list[OutreachLogResponse])
def create_batch_outreach_endpoint(
    request: OutreachBatchRequest,
) -> list[OutreachLogResponse]:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    message = _resolve_project_outreach_message(
        project_id=request.project_id,
        asset_pack_id=request.asset_pack_id,
        channel=request.channel,
    )
    for lead_id in request.lead_ids:
        if get_lead_record(lead_id=lead_id, project_id=request.project_id) is None:
            raise HTTPException(status_code=404, detail=f"Lead not found for project: {lead_id}")

    created_outreach_logs = [
        OutreachLogResponse(
            **create_outreach_log(
                {
                    "project_id": request.project_id,
                    "lead_id": lead_id,
                    "asset_pack_id": request.asset_pack_id,
                    "channel": request.channel,
                    "message": message,
                    "status": "sent",
                }
            )
        )
        for lead_id in request.lead_ids
    ]
    return created_outreach_logs


@router.get("/outreach", response_model=list[OutreachLogResponse])
def list_outreach_endpoint(
    project_id: str | None = None,
    lead_id: str | None = None,
) -> list[OutreachLogResponse]:
    return [
        OutreachLogResponse(**outreach_log)
        for outreach_log in list_outreach_logs(project_id=project_id, lead_id=lead_id)
    ]


@router.patch("/outreach/{outreach_id}", response_model=OutreachLogResponse)
def update_outreach_endpoint(
    outreach_id: str,
    request: OutreachStatusUpdate,
) -> OutreachLogResponse:
    if get_outreach_log_record(outreach_id) is None:
        raise HTTPException(status_code=404, detail="Outreach log not found")

    updated_outreach = update_outreach_status(
        outreach_id=outreach_id,
        status=request.status,
        reply_text=request.reply_text,
    )
    if updated_outreach is None:
        raise HTTPException(status_code=404, detail="Outreach log not found")
    return OutreachLogResponse(**updated_outreach)
