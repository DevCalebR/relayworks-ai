from fastapi import APIRouter, HTTPException

from app.schemas.lead import (
    LeadActivityOutreachItem,
    LeadActivityResponse,
    LeadBatchCreate,
    LeadCreate,
    LeadResponse,
    LeadStatusUpdate,
)
from app.services.memory_service import (
    create_or_get_lead,
    get_lead_record,
    get_project,
    list_leads,
    list_outreach_logs,
    update_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


def _lead_response(lead: dict, deduped: bool = False) -> LeadResponse:
    return LeadResponse(**{**lead, "deduped": deduped})


@router.post("", response_model=LeadResponse)
def create_lead_endpoint(lead: LeadCreate) -> LeadResponse:
    project = get_project(lead.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    created_lead, deduped = create_or_get_lead(
        lead.model_dump() if hasattr(lead, "model_dump") else lead.dict(),
        dedupe=lead.dedupe,
    )
    return _lead_response(created_lead, deduped=deduped)


@router.get("/{lead_id}/activity", response_model=LeadActivityResponse)
def get_lead_activity_endpoint(
    lead_id: str,
    project_id: str | None = None,
) -> LeadActivityResponse:
    lead = get_lead_record(lead_id=lead_id, project_id=project_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    outreach_logs = sorted(
        list_outreach_logs(project_id=str(lead.get("project_id") or ""), lead_id=lead_id),
        key=lambda outreach_log: (
            str(outreach_log.get("created_at") or ""),
            str(outreach_log.get("id") or ""),
        ),
    )
    return LeadActivityResponse(
        lead=LeadResponse(**lead),
        outreach=[
            LeadActivityOutreachItem(
                id=str(outreach_log.get("id") or ""),
                status=str(outreach_log.get("status") or ""),
                channel=str(outreach_log.get("channel") or ""),
                asset_pack_id=str(outreach_log.get("asset_pack_id") or ""),
                message=str(outreach_log.get("message") or ""),
                reply_text=outreach_log.get("reply_text"),
                created_at=str(outreach_log.get("created_at") or ""),
            )
            for outreach_log in outreach_logs
        ],
    )


@router.post("/batch", response_model=list[LeadResponse])
def create_batch_leads_endpoint(request: LeadBatchCreate) -> list[LeadResponse]:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not request.leads:
        raise HTTPException(status_code=400, detail="Leads list must not be empty")

    created_leads = []
    for lead in request.leads:
        payload = {
            "project_id": request.project_id,
            **(
                lead.model_dump()
                if hasattr(lead, "model_dump")
                else lead.dict()
            ),
        }
        created_lead, deduped = create_or_get_lead(payload, dedupe=request.dedupe)
        created_leads.append(_lead_response(created_lead, deduped=deduped))
    return created_leads


@router.get("", response_model=list[LeadResponse])
def list_leads_endpoint(project_id: str | None = None) -> list[LeadResponse]:
    return [LeadResponse(**lead) for lead in list_leads(project_id=project_id)]


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead_status_endpoint(lead_id: str, request: LeadStatusUpdate) -> LeadResponse:
    request_data = request.model_dump(exclude_unset=True) if hasattr(request, "model_dump") else request.dict(exclude_unset=True)
    updated_lead = update_lead(lead_id=lead_id, updates=request_data)
    if updated_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse(**updated_lead)
