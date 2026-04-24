import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate lead/outreach dedupe and lead activity.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()

    suffix = uuid4().hex[:8]
    base_url = args.base_url.rstrip("/")

    single_lead_payload = {
        "project_id": args.project_id,
        "company_name": f"Signal Forge {suffix}",
        "contact_name": "Riley Stone",
        "contact_email": f"riley+{suffix}@signalforge.example",
        "industry": "Revenue enablement consulting",
        "company_description": "Signal Forge helps B2B sales teams tighten pipeline quality and improve coaching.",
        "notes": "Likely cares about cleaner loss-pattern reporting and coaching feedback loops.",
        "dedupe": True,
    }
    batch_payload = {
        "project_id": args.project_id,
        "dedupe": True,
        "leads": [
            {
                "company_name": f"Northstar Ops {suffix}",
                "contact_name": "Avery Cole",
                "contact_email": f"avery+{suffix}@northstar.example",
                "industry": "Revenue operations advisory",
                "company_description": "Northstar Ops helps SaaS teams improve forecasting and pipeline reviews.",
                "notes": "Likely cares about clearer insights from lost deals.",
            },
            {
                "company_name": f"Pipeline Harbor {suffix}",
                "contact_name": "Jordan Lee",
                "contact_email": f"jordan+{suffix}@pipelineharbor.example",
                "industry": "B2B SaaS consulting",
                "company_description": "Pipeline Harbor improves conversion quality and GTM execution for SaaS teams.",
                "notes": "Likely interested in converting closed-lost insight into experiments.",
            },
            {
                "company_name": f"Forecast Current {suffix}",
                "contact_name": "Taylor Brooks",
                "contact_email": f"taylor+{suffix}@forecastcurrent.example",
                "industry": "Revenue analytics consulting",
                "company_description": "Forecast Current helps teams connect deal reviews and forecast accuracy.",
                "notes": "Likely cares about faster insight from stalled opportunities.",
            },
        ],
    }

    with httpx.Client() as client:
        single_first = request_json(client, "POST", f"{base_url}/leads", single_lead_payload)
        single_second = request_json(client, "POST", f"{base_url}/leads", single_lead_payload)
        assert isinstance(single_first, dict)
        assert isinstance(single_second, dict)
        assert single_first["deduped"] is False
        assert single_second["deduped"] is True
        assert single_first["id"] == single_second["id"]

        leads_before_batch = request_json(
            client,
            "GET",
            f"{base_url}/leads?project_id={args.project_id}",
        )
        assert isinstance(leads_before_batch, list)

        batch_first = request_json(client, "POST", f"{base_url}/leads/batch", batch_payload)
        batch_second = request_json(client, "POST", f"{base_url}/leads/batch", batch_payload)
        assert isinstance(batch_first, list)
        assert isinstance(batch_second, list)
        assert len(batch_first) == 3 and len(batch_second) == 3
        assert all(item["deduped"] is False for item in batch_first)
        assert all(item["deduped"] is True for item in batch_second)
        assert [item["id"] for item in batch_first] == [item["id"] for item in batch_second]

        leads_after_batch = request_json(
            client,
            "GET",
            f"{base_url}/leads?project_id={args.project_id}",
        )
        assert isinstance(leads_after_batch, list)
        assert len(leads_after_batch) == len(leads_before_batch) + 3

        asset_pack = request_json(
            client,
            "POST",
            f"{base_url}/agents/asset-pack",
            {"project_id": args.project_id, "use_latest_launch_plan": True},
        )
        assert isinstance(asset_pack, dict)

        draft_payload = {
            "project_id": args.project_id,
            "lead_id": batch_first[0]["id"],
            "asset_pack_id": asset_pack["id"],
            "channel": "email",
            "dedupe": True,
        }
        draft_first = request_json(client, "POST", f"{base_url}/agents/outreach/draft", draft_payload)
        draft_second = request_json(client, "POST", f"{base_url}/agents/outreach/draft", draft_payload)
        assert isinstance(draft_first, dict)
        assert isinstance(draft_second, dict)
        assert draft_first["deduped"] is False
        assert draft_second["deduped"] is True
        assert draft_first["id"] == draft_second["id"]

        batch_draft_payload = {
            "project_id": args.project_id,
            "lead_ids": [item["id"] for item in batch_first],
            "asset_pack_id": asset_pack["id"],
            "channel": "email",
            "dedupe": True,
        }
        batch_draft_first = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/draft/batch",
            batch_draft_payload,
        )
        batch_draft_second = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/draft/batch",
            batch_draft_payload,
        )
        assert isinstance(batch_draft_first, list)
        assert isinstance(batch_draft_second, list)
        assert len(batch_draft_first) == 3 and len(batch_draft_second) == 3
        assert batch_draft_first[0]["id"] == draft_first["id"]
        assert batch_draft_first[0]["deduped"] is True
        assert all(item["deduped"] is True for item in batch_draft_second)
        assert [item["id"] for item in batch_draft_first] == [item["id"] for item in batch_draft_second]

        mark_sent = request_json(
            client,
            "POST",
            f"{base_url}/agents/outreach/{batch_draft_first[1]['id']}/mark-sent",
            {"mark_lead_contacted": True},
        )
        assert isinstance(mark_sent, dict)
        assert mark_sent["outreach"]["status"] == "sent"
        assert mark_sent["lead"]["status"] == "contacted"

        activity = request_json(
            client,
            "GET",
            f"{base_url}/leads/{batch_first[1]['id']}/activity?project_id={args.project_id}",
        )
        assert isinstance(activity, dict)
        assert activity["lead"]["id"] == batch_first[1]["id"]
        created_at_values = [item["created_at"] for item in activity["outreach"]]
        assert created_at_values == sorted(created_at_values)
        assert any(item["status"] == "sent" for item in activity["outreach"])
        assert all("message" in item for item in activity["outreach"])
        assert all("reply_text" in item for item in activity["outreach"])

    print(
        json.dumps(
            {
                "single_first": single_first,
                "single_second": single_second,
                "batch_first": batch_first,
                "batch_second": batch_second,
                "draft_first": draft_first,
                "draft_second": draft_second,
                "batch_draft_first": batch_draft_first,
                "batch_draft_second": batch_draft_second,
                "mark_sent": mark_sent,
                "activity": activity,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
