from fastapi import APIRouter, HTTPException

from app.schemas.asset_pack import AssetPackRequest, AssetPackResponse
from app.schemas.launch_plan import LaunchPlanRequest, LaunchPlanResponse
from app.schemas.lead import LeadResponse
from app.schemas.outreach import (
    OutreachBatchRequest,
    OutreachLogResponse,
    OutreachMarkSentRequest,
    OutreachMarkSentResponse,
    OutreachRequest,
    OutreachStatusUpdate,
)
from app.schemas.run import CompareResponse, OperatorMode, RunRequest, RunResponse
from app.services.asset_pack_agent import generate_asset_pack
from app.services.launch_plan_agent import generate_launch_plan
from app.services.personalization_agent import generate_personalized_outreach
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
    update_lead,
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


def _get_project_asset_pack(
    project_id: str,
    asset_pack_id: str,
) -> dict:
    asset_pack = get_asset_pack_record(
        asset_pack_id=asset_pack_id,
        project_id=project_id,
    )
    if asset_pack is None:
        raise HTTPException(status_code=404, detail="Asset pack not found for project")
    return asset_pack


def _create_outreach_record(
    project_id: str,
    lead_id: str,
    asset_pack_id: str,
    channel: str,
    status: str = "sent",
) -> dict:
    lead = get_lead_record(lead_id=lead_id, project_id=project_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead not found for project: {lead_id}")

    asset_pack = _get_project_asset_pack(project_id=project_id, asset_pack_id=asset_pack_id)
    message, _generation_mode = generate_personalized_outreach(
        lead=lead,
        asset_pack=asset_pack,
        channel=channel,
    )
    return create_outreach_log(
        {
            "project_id": project_id,
            "lead_id": lead_id,
            "asset_pack_id": asset_pack_id,
            "channel": channel,
            "message": message,
            "status": status,
        }
    )


def _validate_project(project_id: str) -> None:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")


def _get_project_leads(project_id: str, lead_ids: list[str]) -> dict[str, dict]:
    leads_by_id: dict[str, dict] = {}
    for lead_id in lead_ids:
        lead = get_lead_record(lead_id=lead_id, project_id=project_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead not found for project: {lead_id}")
        leads_by_id[lead_id] = lead
    return leads_by_id


@router.post("/outreach", response_model=OutreachLogResponse)
def create_outreach_endpoint(request: OutreachRequest) -> OutreachLogResponse:
    _validate_project(request.project_id)

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
    _validate_project(request.project_id)
    if not request.lead_ids:
        raise HTTPException(status_code=400, detail="Lead IDs list must not be empty")

    asset_pack = _get_project_asset_pack(
        project_id=request.project_id,
        asset_pack_id=request.asset_pack_id,
    )
    leads_by_id = _get_project_leads(project_id=request.project_id, lead_ids=request.lead_ids)

    created_outreach_logs = [
        OutreachLogResponse(
            **create_outreach_log(
                {
                    "project_id": request.project_id,
                    "lead_id": lead_id,
                    "asset_pack_id": request.asset_pack_id,
                    "channel": request.channel,
                    "message": generate_personalized_outreach(
                        lead=leads_by_id.get(lead_id) or {},
                        asset_pack=asset_pack,
                        channel=request.channel,
                    )[0],
                    "status": "sent",
                }
            )
        )
        for lead_id in request.lead_ids
    ]
    return created_outreach_logs


@router.post("/outreach/draft", response_model=OutreachLogResponse)
def create_outreach_draft_endpoint(request: OutreachRequest) -> OutreachLogResponse:
    _validate_project(request.project_id)

    outreach_log = _create_outreach_record(
        project_id=request.project_id,
        lead_id=request.lead_id,
        asset_pack_id=request.asset_pack_id,
        channel=request.channel,
        status="draft",
    )
    return OutreachLogResponse(**outreach_log)


@router.post("/outreach/draft/batch", response_model=list[OutreachLogResponse])
def create_batch_outreach_draft_endpoint(
    request: OutreachBatchRequest,
) -> list[OutreachLogResponse]:
    _validate_project(request.project_id)
    if not request.lead_ids:
        raise HTTPException(status_code=400, detail="Lead IDs list must not be empty")

    asset_pack = _get_project_asset_pack(
        project_id=request.project_id,
        asset_pack_id=request.asset_pack_id,
    )
    leads_by_id = _get_project_leads(project_id=request.project_id, lead_ids=request.lead_ids)

    created_outreach_logs = [
        OutreachLogResponse(
            **create_outreach_log(
                {
                    "project_id": request.project_id,
                    "lead_id": lead_id,
                    "asset_pack_id": request.asset_pack_id,
                    "channel": request.channel,
                    "message": generate_personalized_outreach(
                        lead=leads_by_id.get(lead_id) or {},
                        asset_pack=asset_pack,
                        channel=request.channel,
                    )[0],
                    "status": "draft",
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


@router.post("/outreach/{outreach_id}/mark-sent", response_model=OutreachMarkSentResponse)
def mark_outreach_sent_endpoint(
    outreach_id: str,
    request: OutreachMarkSentRequest,
) -> OutreachMarkSentResponse:
    outreach_log = get_outreach_log_record(outreach_id)
    if outreach_log is None:
        raise HTTPException(status_code=404, detail="Outreach log not found")

    updated_outreach = update_outreach_status(outreach_id=outreach_id, status="sent")
    if updated_outreach is None:
        raise HTTPException(status_code=404, detail="Outreach log not found")

    updated_lead = None
    if request.mark_lead_contacted:
        updated_lead = update_lead(
            lead_id=str(updated_outreach.get("lead_id") or ""),
            updates={"status": "contacted"},
        )

    return OutreachMarkSentResponse(
        outreach=OutreachLogResponse(**updated_outreach),
        lead=LeadResponse(**updated_lead) if updated_lead is not None else None,
    )


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
