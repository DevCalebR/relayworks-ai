import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_compare(base_url: str, project_id: str, mode: str | None = None) -> dict:
    query = {"project_id": project_id}
    if mode is not None:
        query["mode"] = mode
    url = f"{base_url.rstrip('/')}/agents/compare?{urlencode(query)}"
    with urlopen(url) as response:
        return json.load(response)


def assert_compare_response(payload: dict, expected_project_id: str) -> None:
    assert payload["project_id"] == expected_project_id

    ranked = payload["ranked_opportunities"]
    total_runs = payload["total_runs"]
    total_opportunities = payload["total_opportunities"]

    assert total_runs >= total_opportunities
    assert total_opportunities == len(ranked)

    if not ranked:
        assert payload["top_opportunity"] is None
        assert payload["message"]
        return

    assert payload["top_opportunity"] == ranked[0]
    previous_key = None
    required_fields = {
        "title",
        "niche",
        "target_customer",
        "core_problem",
        "offer",
        "mvp",
        "distribution_channel",
        "monetization_model",
        "opportunity_score",
        "confidence_score",
        "reasoning",
        "next_actions",
        "run_id",
        "mode",
        "created_at",
    }

    for item in ranked:
        assert required_fields.issubset(item)
        current_key = (item["opportunity_score"], item["confidence_score"])
        if previous_key is not None:
            assert current_key <= previous_key
        previous_key = current_key


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--mode")
    args = parser.parse_args()

    try:
        payload = fetch_compare(args.base_url, args.project_id, args.mode)
        assert_compare_response(payload, args.project_id)
    except (AssertionError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}")
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
