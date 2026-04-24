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


def fetch_json(client: httpx.Client, method: str, url: str, payload: dict | None = None) -> dict | list:
    response = client.request(method, url, json=payload, timeout=30.0)
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate personalized outreach and follow-ups.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--lead-id", required=True)
    parser.add_argument("--original-outreach-id", required=True)
    parser.add_argument("--follow-up-id", required=True)
    parser.add_argument("--reply-follow-up-id", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    with httpx.Client() as client:
        leads = fetch_json(client, "GET", f"{base_url}/leads?project_id={args.project_id}")
        outreach_logs = fetch_json(
            client,
            "GET",
            f"{base_url}/agents/outreach?project_id={args.project_id}&lead_id={args.lead_id}",
        )

    lead = next(item for item in leads if item["id"] == args.lead_id)
    original = next(item for item in outreach_logs if item["id"] == args.original_outreach_id)
    follow_up = next(item for item in outreach_logs if item["id"] == args.follow_up_id)
    reply_follow_up = next(item for item in outreach_logs if item["id"] == args.reply_follow_up_id)

    assert original["message"] != follow_up["message"]
    assert follow_up["message"] != reply_follow_up["message"]
    for item in (original, follow_up, reply_follow_up):
        assert message_has_context_signal(item["message"], lead)
        assert message_has_no_placeholders(item["message"])

    assert "timing is tight" in str(follow_up.get("reply_text") or "").lower() or "timing is tight" in str(original.get("reply_text") or "").lower() or "timing is tight" in str(reply_follow_up.get("message") or "").lower()

    persisted = json.loads((Path(__file__).resolve().parents[1] / "data" / "outreach_logs.json").read_text(encoding="utf-8"))
    for outreach_id in (args.original_outreach_id, args.follow_up_id, args.reply_follow_up_id):
        assert any(item["id"] == outreach_id for item in persisted)

    print(
        json.dumps(
            {
                "lead": lead,
                "original_outreach": original,
                "follow_up": follow_up,
                "reply_follow_up": reply_follow_up,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
