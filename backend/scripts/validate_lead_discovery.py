import argparse
import json
from pathlib import Path
import sys

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
    response = client.request(method, url, json=payload, timeout=90.0)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    return response.text


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate candidate lead discovery workflow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    discover_payload = {
        "project_id": args.project_id,
        "target": (
            "Seed to Series B B2B SaaS companies likely to care about win-loss analysis, "
            "revenue operations, sales process improvement, and closed-lost learning loops"
        ),
        "count": 5,
    }

    with httpx.Client() as client:
        root = request_json(client, "GET", f"{base_url}/")
        health = request_json(client, "GET", f"{base_url}/health")
        discovered = request_json(client, "POST", f"{base_url}/leads/discover", discover_payload)
        assert isinstance(discovered, list)
        assert len(discovered) == 5
        assert all(item["status"] == "discovered" for item in discovered)
        assert all(1 <= int(item["confidence_score"]) <= 10 for item in discovered)
        assert all("fit_reason" in item and item["fit_reason"] for item in discovered)
        assert all(item.get("contact_email") in (None, "") for item in discovered)
        assert all(item.get("contact_name") in (None, "") for item in discovered)
        assert all(
            str(item.get("lead_source") or "").startswith("openai_")
            or str(item.get("lead_source") or "").startswith("fallback_example:")
            for item in discovered
        )

        listed_candidates = request_json(
            client,
            "GET",
            f"{base_url}/leads/candidates?project_id={args.project_id}",
        )
        assert isinstance(listed_candidates, list)
        discovered_ids = {item["id"] for item in discovered}
        listed_lookup = {item["id"]: item for item in listed_candidates if item["id"] in discovered_ids}
        assert discovered_ids.issubset(set(listed_lookup))

        imported_response = request_json(
            client,
            "POST",
            f"{base_url}/leads/candidates/{discovered[0]['id']}/import",
        )
        assert isinstance(imported_response, dict)
        assert imported_response["candidate_lead"]["status"] == "imported"
        assert imported_response["lead"]["project_id"] == args.project_id
        assert imported_response["lead"]["company_name"] == discovered[0]["company_name"]
        if discovered[0]["contact_email"] in (None, ""):
            assert "Candidate fit reason:" in str(imported_response["lead"].get("notes") or "")
            assert "Candidate lead source:" in str(imported_response["lead"].get("notes") or "")

        rejected_response = request_json(
            client,
            "POST",
            f"{base_url}/leads/candidates/{discovered[1]['id']}/reject",
        )
        assert isinstance(rejected_response, dict)
        assert rejected_response["status"] == "rejected"

        leads = request_json(client, "GET", f"{base_url}/leads?project_id={args.project_id}")
        assert isinstance(leads, list)
        assert any(lead["company_name"] == discovered[0]["company_name"] for lead in leads)

        candidates_after = request_json(
            client,
            "GET",
            f"{base_url}/leads/candidates?project_id={args.project_id}",
        )
        assert isinstance(candidates_after, list)
        candidates_after_lookup = {item["id"]: item for item in candidates_after if item["id"] in discovered_ids}
        assert candidates_after_lookup[discovered[0]["id"]]["status"] == "imported"
        assert candidates_after_lookup[discovered[1]["id"]]["status"] == "rejected"
        for candidate_id in [item["id"] for item in discovered[2:]]:
            assert candidates_after_lookup[candidate_id]["status"] == "discovered"

    persisted_candidates = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "candidate_leads.json").read_text(
            encoding="utf-8"
        )
    )
    persisted_lookup = {item["id"]: item for item in persisted_candidates if item["id"] in discovered_ids}
    assert persisted_lookup[discovered[0]["id"]]["status"] == "imported"
    assert persisted_lookup[discovered[1]["id"]]["status"] == "rejected"

    print(
        json.dumps(
            {
                "root": root,
                "health": health,
                "discovered": discovered,
                "imported_response": imported_response,
                "rejected_response": rejected_response,
                "candidates_after": [candidates_after_lookup[item["id"]] for item in discovered],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
