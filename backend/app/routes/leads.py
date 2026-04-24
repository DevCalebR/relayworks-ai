from fastapi import APIRouter, HTTPException

from app.schemas.lead import LeadBatchCreate, LeadCreate, LeadResponse, LeadStatusUpdate
from app.services.memory_service import create_lead, get_project, list_leads, update_lead

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


@router.post("/batch", response_model=list[LeadResponse])
def create_batch_leads_endpoint(request: LeadBatchCreate) -> list[LeadResponse]:
    project = get_project(request.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not request.leads:
        raise HTTPException(status_code=400, detail="Leads list must not be empty")

    created_leads = [
        LeadResponse(
            **create_lead(
                {
                    "project_id": request.project_id,
                    **(
                        lead.model_dump()
                        if hasattr(lead, "model_dump")
                        else lead.dict()
                    ),
                }
            )
        )
        for lead in request.leads
    ]
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
