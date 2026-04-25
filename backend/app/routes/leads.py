from fastapi import APIRouter, HTTPException

from app.schemas.lead import (
    CandidateLeadDiscoverRequest,
    CandidateLeadImportResponse,
    CandidateLeadResponse,
    LeadActivityOutreachItem,
    LeadActivityResponse,
    LeadBatchCreate,
    LeadCreate,
    LeadResponse,
    LeadStatusUpdate,
)
from app.services.lead_discovery import discover_candidate_leads
from app.services.memory_service import (
    create_or_get_lead,
    get_candidate_lead_record,
    get_lead_record,
    get_project,
    list_candidate_leads,
    list_leads,
    list_outreach_logs,
    update_candidate_lead_status,
    update_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


def _lead_response(lead: dict, deduped: bool = False) -> LeadResponse:
    return LeadResponse(**{**lead, "deduped": deduped})


def _candidate_response(candidate_lead: dict) -> CandidateLeadResponse:
    return CandidateLeadResponse(**candidate_lead)


def _candidate_notes(candidate_lead: dict) -> str:
    note_parts = [
        f"Candidate fit reason: {str(candidate_lead.get('fit_reason') or '').strip()}",
    ]
    contact_title = str(candidate_lead.get("contact_title") or "").strip()
    lead_source = str(candidate_lead.get("lead_source") or "").strip()
    linkedin_url = str(candidate_lead.get("linkedin_url") or "").strip()
    if contact_title:
        note_parts.append(f"Candidate contact title: {contact_title}")
    if lead_source:
        note_parts.append(f"Candidate lead source: {lead_source}")
    if linkedin_url:
        note_parts.append(f"Candidate LinkedIn URL: {linkedin_url}")
    return "\n".join(note_parts)


def _merge_notes(existing_notes: str | None, candidate_notes: str) -> str:
    normalized_existing = str(existing_notes or "").strip()
    if not normalized_existing:
        return candidate_notes
    if candidate_notes in normalized_existing:
        return normalized_existing
    return f"{normalized_existing}\n\n{candidate_notes}"


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


@router.post("/discover", response_model=list[CandidateLeadResponse])
def discover_leads_endpoint(request: CandidateLeadDiscoverRequest) -> list[CandidateLeadResponse]:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    discovered = discover_candidate_leads(
        project_id=request.project_id,
        target=request.target,
        count=request.count,
        mode=request.mode,
    )
    return [_candidate_response(candidate_lead) for candidate_lead in discovered]


@router.get("/candidates", response_model=list[CandidateLeadResponse])
def list_candidate_leads_endpoint(
    project_id: str | None = None,
    status: str | None = None,
) -> list[CandidateLeadResponse]:
    return [
        _candidate_response(candidate_lead)
        for candidate_lead in list_candidate_leads(project_id=project_id, status=status)
    ]


@router.post("/candidates/{candidate_lead_id}/import", response_model=CandidateLeadImportResponse)
def import_candidate_lead_endpoint(candidate_lead_id: str) -> CandidateLeadImportResponse:
    candidate_lead = get_candidate_lead_record(candidate_lead_id)
    if candidate_lead is None:
        raise HTTPException(status_code=404, detail="Candidate lead not found")
    if str(candidate_lead.get("status") or "") == "imported":
        raise HTTPException(status_code=400, detail="Candidate lead already imported")

    if get_project(str(candidate_lead.get("project_id") or "")) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    created_lead, deduped = create_or_get_lead(
        {
            "project_id": str(candidate_lead.get("project_id") or ""),
            "company_name": str(candidate_lead.get("company_name") or ""),
            "contact_name": str(candidate_lead.get("contact_name") or ""),
            "contact_email": str(candidate_lead.get("contact_email") or ""),
            "company_description": candidate_lead.get("company_description"),
            "industry": candidate_lead.get("industry"),
            "website": candidate_lead.get("website"),
            "notes": _candidate_notes(candidate_lead),
            "status": "new",
        },
        dedupe=True,
    )
    created_lead = update_lead(
        lead_id=str(created_lead.get("id") or ""),
        updates={
            "company_description": candidate_lead.get("company_description"),
            "industry": candidate_lead.get("industry"),
            "website": candidate_lead.get("website"),
            "notes": _merge_notes(created_lead.get("notes"), _candidate_notes(candidate_lead)),
        },
    ) or created_lead
    updated_candidate = update_candidate_lead_status(candidate_lead_id, "imported")
    if updated_candidate is None:
        raise HTTPException(status_code=404, detail="Candidate lead not found")
    return CandidateLeadImportResponse(
        candidate_lead=_candidate_response(updated_candidate),
        lead=_lead_response(created_lead, deduped=deduped),
    )


@router.post("/candidates/{candidate_lead_id}/reject", response_model=CandidateLeadResponse)
def reject_candidate_lead_endpoint(candidate_lead_id: str) -> CandidateLeadResponse:
    existing_candidate = get_candidate_lead_record(candidate_lead_id)
    if existing_candidate is None:
        raise HTTPException(status_code=404, detail="Candidate lead not found")
    if str(existing_candidate.get("status") or "") == "imported":
        raise HTTPException(status_code=400, detail="Imported candidate leads cannot be rejected")

    updated_candidate = update_candidate_lead_status(candidate_lead_id, "rejected")
    if updated_candidate is None:
        raise HTTPException(status_code=404, detail="Candidate lead not found")
    return _candidate_response(updated_candidate)


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
