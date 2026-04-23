import argparse
import json
from urllib.parse import urlencode

import httpx


REQUIRED_FIELDS = {
    "id",
    "project_id",
    "launch_plan_id",
    "source_run_id",
    "headline",
    "one_sentence_pitch",
    "landing_page_hero",
    "landing_page_subheadline",
    "key_benefits",
    "offer_stack",
    "call_to_action",
    "cold_outreach_email_subject",
    "cold_outreach_email_body",
    "linkedin_dm",
    "discovery_call_script",
    "pilot_offer",
    "pricing_blurb",
    "faq",
    "created_at",
}
NON_EMPTY_LIST_FIELDS = {"key_benefits", "offer_stack", "discovery_call_script"}


def get_json(url: str) -> dict | list:
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()


def assert_asset_pack(payload: dict, project_id: str, launch_plan_id: str) -> None:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in payload)
    if missing:
        raise AssertionError(f"Missing required fields: {missing}")

    if payload["project_id"] != project_id:
        raise AssertionError(
            f"Expected project_id={project_id!r}, got {payload['project_id']!r}"
        )
    if payload["launch_plan_id"] != launch_plan_id:
        raise AssertionError(
            f"Expected launch_plan_id={launch_plan_id!r}, got {payload['launch_plan_id']!r}"
        )

    for field in NON_EMPTY_LIST_FIELDS:
        value = payload.get(field)
        if not isinstance(value, list) or not value:
            raise AssertionError(f"{field} must be a non-empty list")

    faq = payload.get("faq")
    if not isinstance(faq, list) or not faq:
        raise AssertionError("faq must be a non-empty list")
    for item in faq:
        if not isinstance(item, dict):
            raise AssertionError("faq items must be objects")
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if not question or not answer:
            raise AssertionError("faq items must include question and answer")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate asset-pack retrieval endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--launch-plan-id", required=True)
    parser.add_argument("--asset-pack-id", required=True)
    args = parser.parse_args()

    asset_packs_url = f"{args.base_url.rstrip('/')}/agents/asset-packs"
    all_records = get_json(asset_packs_url)
    if not isinstance(all_records, list):
        raise AssertionError("Expected list response from /agents/asset-packs")

    matching_ids = {record.get("id") for record in all_records if isinstance(record, dict)}
    if args.asset_pack_id not in matching_ids:
        raise AssertionError(f"Asset pack {args.asset_pack_id} not found in full list")

    by_project = get_json(
        f"{asset_packs_url}?{urlencode({'project_id': args.project_id})}"
    )
    if not isinstance(by_project, list) or not by_project:
        raise AssertionError("Expected non-empty project-filtered asset-pack list")

    by_launch_plan = get_json(
        f"{asset_packs_url}?{urlencode({'launch_plan_id': args.launch_plan_id})}"
    )
    if not isinstance(by_launch_plan, list) or not by_launch_plan:
        raise AssertionError("Expected non-empty launch-plan-filtered asset-pack list")

    target = None
    for record in by_launch_plan:
        if isinstance(record, dict) and record.get("id") == args.asset_pack_id:
            target = record
            break
    if target is None:
        raise AssertionError("Expected target asset pack in launch-plan filtered results")

    assert_asset_pack(target, args.project_id, args.launch_plan_id)
    print(json.dumps(target, indent=2))


if __name__ == "__main__":
    main()
