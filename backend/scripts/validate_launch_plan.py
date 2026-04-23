import argparse
import json
from urllib.parse import urlencode
from urllib.request import urlopen


REQUIRED_LIST_FIELDS = [
    "mvp_scope",
    "acquisition_channels",
    "first_30_day_plan",
    "success_metrics",
    "biggest_risks",
    "mitigation_steps",
]

REQUIRED_TEXT_FIELDS = [
    "headline",
    "ideal_customer_profile",
    "painful_problem_statement",
    "offer_summary",
    "pricing_hypothesis",
    "sales_motion",
    "launch_recommendation",
    "created_at",
]


def get_json(url: str) -> dict | list:
    with urlopen(url) as response:
        return json.load(response)


def assert_launch_plan(payload: dict, project_id: str, run_id: str) -> None:
    assert payload["project_id"] == project_id
    assert payload["source_run_id"] == run_id
    assert isinstance(payload["selected_opportunity"], dict) and payload["selected_opportunity"]
    for field in REQUIRED_TEXT_FIELDS:
        assert isinstance(payload.get(field), str) and payload[field].strip()
    for field in REQUIRED_LIST_FIELDS:
        assert isinstance(payload.get(field), list) and payload[field]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    launch_plan_url = f"{args.base_url.rstrip('/')}/agents/launch-plans"
    payload = get_json(f"{launch_plan_url}?{urlencode({'run_id': args.run_id})}")
    assert isinstance(payload, list) and payload
    assert_launch_plan(payload[0], args.project_id, args.run_id)

    project_payload = get_json(
        f"{launch_plan_url}?{urlencode({'project_id': args.project_id})}"
    )
    assert isinstance(project_payload, list) and project_payload
    assert any(item["source_run_id"] == args.run_id for item in project_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
