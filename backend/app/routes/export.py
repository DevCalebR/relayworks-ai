import csv
from io import StringIO

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.services.memory_service import list_leads, list_outreach_logs

router = APIRouter(prefix="/export", tags=["export"])


def _render_csv(fieldnames: list[str], rows: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


@router.get("/leads", response_class=PlainTextResponse)
def export_leads_endpoint(project_id: str) -> PlainTextResponse:
    leads = list_leads(project_id=project_id)
    csv_text = _render_csv(
        fieldnames=[
            "id",
            "company_name",
            "contact_name",
            "contact_email",
            "status",
            "created_at",
        ],
        rows=[
            {
                "id": lead.get("id", ""),
                "company_name": lead.get("company_name", ""),
                "contact_name": lead.get("contact_name", ""),
                "contact_email": lead.get("contact_email", ""),
                "status": lead.get("status", ""),
                "created_at": lead.get("created_at", ""),
            }
            for lead in leads
        ],
    )
    return PlainTextResponse(csv_text, media_type="text/csv")


@router.get("/outreach", response_class=PlainTextResponse)
def export_outreach_endpoint(project_id: str) -> PlainTextResponse:
    outreach_logs = list_outreach_logs(project_id=project_id)
    csv_text = _render_csv(
        fieldnames=["id", "lead_id", "channel", "status", "created_at"],
        rows=[
            {
                "id": outreach_log.get("id", ""),
                "lead_id": outreach_log.get("lead_id", ""),
                "channel": outreach_log.get("channel", ""),
                "status": outreach_log.get("status", ""),
                "created_at": outreach_log.get("created_at", ""),
            }
            for outreach_log in outreach_logs
        ],
    )
    return PlainTextResponse(csv_text, media_type="text/csv")
