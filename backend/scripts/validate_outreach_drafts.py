import argparse
import json
from pathlib import Path
import sys

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.personalization_agent import (
    message_has_context_signal,
    message_has_no_placeholders,
)


def request_json(
    client: httpx.Client,
    method: str,
    url: str,
    payload: dict | None = None,
) -> dict | list | str:
    response = client.request(method, url, json=payload, timeout=30.0)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    return response.text


def _first_name(contact_name: str) -> str:
    return next((part.strip(" ,.") for part in contact_name.split() if part.strip(" ,.")), "")


def _assert_message_quality(message: str, lead: dict) -> None:
    first_name = _first_name(str(lead.get("contact_name") or ""))
    assert message_has_context_signal(message, lead)
    assert message_has_no_placeholders(message)
    if first_name:
        assert f"Hi {first_name}," in message


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate outreach draft workflow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--asset-pack-id", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    leads_payload = {
        "project_id": args.project_id,
        "leads": [
            {
                "company_name": "Summit Revenue Partners",
                "contact_name": "Elena Morris",
                "contact_email": "elena@summitrev.example",
                "industry": "Revenue operations consulting",
                "company_description": "Summit Revenue Partners helps B2B SaaS teams improve forecasting, pipeline visibility, and win rates.",
                "notes": "Likely cares about lost-deal analysis and faster GTM learning loops.",
            },
            {
                "company_name": "Atlas Growth Systems",
                "contact_name": "Maya Chen",
                "contact_email": "maya@atlasgrowth.example",
                "industry": "B2B SaaS growth consulting",
                "company_description": "Atlas Growth Systems helps SaaS teams improve pipeline conversion and sales process quality.",
                "notes": "Likely interested in turning closed-lost data into GTM experiments.",
            },
            {
                "company_name": "Beacon Revenue Ops",
                "contact_name": "Jon Rivera",
                "contact_email": "jon@beaconrevops.example",
                "industry": "Revenue operations advisory",
                "company_description": "Beacon Revenue Ops supports SaaS revenue teams with forecasting, deal review, and operating cadence.",
                "notes": "Likely cares about better qualitative insight from lost and stalled deals.",
            },
        ],
    }

    with httpx.Client() as client:
        created_leads = request_json(client, "POST", f"{base_url}/leads/batch", leads_payload)
        assert isinstance(created_leads, list)
        assert len(created_leads) == 3
        assert all(lead["status"] == "new" for lead in created_leads)

        single_draft = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/draft",
            {
                "project_id": args.project_id,
                "lead_id": created_leads[0]["id"],
                "asset_pack_id": args.asset_pack_id,
                "channel": "email",
            },
        )
        assert isinstance(single_draft, dict)
        assert single_draft["status"] == "draft"

        batch_drafts = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/draft/batch",
            {
                "project_id": args.project_id,
                "lead_ids": [lead["id"] for lead in created_leads],
                "asset_pack_id": args.asset_pack_id,
                "channel": "email",
            },
        )
        assert isinstance(batch_drafts, list)
        assert len(batch_drafts) == 3
        assert all(item["status"] == "draft" for item in batch_drafts)

        all_leads = request_json(client, "GET", f"{base_url}/leads?project_id={args.project_id}")
        assert isinstance(all_leads, list)
        lead_lookup = {lead["id"]: lead for lead in all_leads if lead["id"] in {item["id"] for item in created_leads}}
        assert len(lead_lookup) == 3
        assert all(lead["status"] == "new" for lead in lead_lookup.values())

        for outreach in [single_draft, *batch_drafts]:
            lead = lead_lookup[outreach["lead_id"]]
            _assert_message_quality(outreach["message"], lead)

        pre_mark_follow_ups = request_json(
            client,
            "GET",
            f"{base_url}/pipeline/follow-ups?project_id={args.project_id}",
        )
        assert isinstance(pre_mark_follow_ups, list)
        assert all(item["lead_id"] != created_leads[0]["id"] for item in pre_mark_follow_ups)

        marked_outreach = batch_drafts[1]
        mark_sent_response = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/{marked_outreach['id']}/mark-sent",
            {"mark_lead_contacted": True},
        )
        assert isinstance(mark_sent_response, dict)
        assert mark_sent_response["outreach"]["status"] == "sent"
        assert mark_sent_response["lead"]["status"] == "contacted"

        metrics = request_json(client, "GET", f"{base_url}/pipeline/metrics?project_id={args.project_id}")
        follow_ups = request_json(
            client,
            "GET",
            f"{base_url}/pipeline/follow-ups?project_id={args.project_id}",
        )
        outreach_export = request_json(
            client,
            "GET",
            f"{base_url}/export/outreach?project_id={args.project_id}",
        )

    assert isinstance(metrics, dict)
    assert metrics["outreach_counts"]["draft"] >= 3
    assert metrics["outreach_counts"]["sent"] >= 1
    assert isinstance(follow_ups, list)
    assert any(item["last_outreach_id"] == marked_outreach["id"] for item in follow_ups)
    assert all(item["lead_id"] != created_leads[0]["id"] for item in follow_ups)
    assert isinstance(outreach_export, str)
    assert "draft" in outreach_export and "sent" in outreach_export

    data_dir = Path(__file__).resolve().parents[1] / "data"
    persisted_leads = json.loads((data_dir / "leads.json").read_text(encoding="utf-8"))
    persisted_outreach = json.loads((data_dir / "outreach_logs.json").read_text(encoding="utf-8"))

    assert any(item["id"] == created_leads[1]["id"] and item["status"] == "contacted" for item in persisted_leads)
    assert any(item["id"] == created_leads[0]["id"] and item["status"] == "new" for item in persisted_leads)
    for outreach_id in [single_draft["id"], *(item["id"] for item in batch_drafts)]:
        assert any(item["id"] == outreach_id for item in persisted_outreach)

    print(
        json.dumps(
            {
                "created_leads": created_leads,
                "single_draft": single_draft,
                "batch_drafts": batch_drafts,
                "mark_sent_response": mark_sent_response,
                "metrics": metrics,
                "follow_ups": follow_ups,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
