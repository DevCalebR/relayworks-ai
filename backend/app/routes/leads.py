from fastapi import APIRouter, HTTPException

from app.schemas.lead import LeadCreate, LeadResponse, LeadStatusUpdate
from app.services.memory_service import create_lead, get_project, list_leads, update_lead_status

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
def create_lead_endpoint(lead: LeadCreate) -> LeadResponse:
    project = get_project(lead.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    created_lead = create_lead(
        lead.model_dump() if hasattr(lead, "model_dump") else lead.dict()
    )
    return LeadResponse(**created_lead)


@router.get("", response_model=list[LeadResponse])
def list_leads_endpoint(project_id: str | None = None) -> list[LeadResponse]:
    return [LeadResponse(**lead) for lead in list_leads(project_id=project_id)]


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead_status_endpoint(lead_id: str, request: LeadStatusUpdate) -> LeadResponse:
    updated_lead = update_lead_status(lead_id=lead_id, status=request.status)
    if updated_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse(**updated_lead)
