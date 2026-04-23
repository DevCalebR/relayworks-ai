from fastapi import APIRouter, HTTPException

from app.schemas.lead import LeadCreate, LeadResponse
from app.services.memory_service import create_lead, get_project, list_leads

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
