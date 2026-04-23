import argparse
import json
from pathlib import Path

import httpx


def get_json(client: httpx.Client, url: str) -> dict | list:
    response = client.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()


def patch_json(client: httpx.Client, url: str, payload: dict) -> dict:
    response = client.patch(url, json=payload, timeout=30.0)
    response.raise_for_status()
    return response.json()


def assert_counts(metrics: dict) -> None:
    lead_counts = metrics["lead_counts"]
    outreach_counts = metrics["outreach_counts"]

    assert lead_counts["total"] == (
        lead_counts["new"]
        + lead_counts["contacted"]
        + lead_counts["replied"]
        + lead_counts["interested"]
        + lead_counts["closed"]
    )
    assert outreach_counts["total"] == (
        outreach_counts["sent"] + outreach_counts["replied"] + outreach_counts["ignored"]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pipeline status updates and metrics.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--lead-id", required=True)
    parser.add_argument("--outreach-id", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    with httpx.Client() as client:
        updated_lead = patch_json(
            client,
            f"{base_url}/leads/{args.lead_id}",
            {"status": "contacted"},
        )
        updated_outreach = patch_json(
            client,
            f"{base_url}/agents/outreach/{args.outreach_id}",
            {"status": "replied"},
        )
        leads = get_json(client, f"{base_url}/leads?project_id={args.project_id}")
        outreach_logs = get_json(client, f"{base_url}/agents/outreach?project_id={args.project_id}")
        metrics = get_json(client, f"{base_url}/pipeline/metrics?project_id={args.project_id}")

    data_dir = Path(__file__).resolve().parents[1] / "data"
    persisted_leads = json.loads((data_dir / "leads.json").read_text(encoding="utf-8"))
    persisted_outreach = json.loads((data_dir / "outreach_logs.json").read_text(encoding="utf-8"))

    assert updated_lead["status"] == "contacted"
    assert updated_outreach["status"] == "replied"
    assert any(lead["id"] == args.lead_id and lead["status"] == "contacted" for lead in leads)
    assert any(
        outreach["id"] == args.outreach_id and outreach["status"] == "replied"
        for outreach in outreach_logs
    )
    assert any(
        lead["id"] == args.lead_id and lead["status"] == "contacted" for lead in persisted_leads
    )
    assert any(
        outreach["id"] == args.outreach_id and outreach["status"] == "replied"
        for outreach in persisted_outreach
    )
    assert_counts(metrics)
    assert metrics["project_id"] == args.project_id

    print(
        json.dumps(
            {
                "updated_lead": updated_lead,
                "updated_outreach": updated_outreach,
                "metrics": metrics,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
