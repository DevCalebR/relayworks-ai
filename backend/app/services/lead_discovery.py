import json

from app.services.memory_service import (
    create_candidate_lead,
    get_latest_launch_plan,
    list_asset_packs,
)
from app.services.research_agent import generate_openai_text


def _extract_json_payload(raw_text: str) -> dict | list | None:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    for start_char, end_char in (("{", "}"), ("[", "]")):
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start == -1 or end == -1 or start > end:
            continue
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, (dict, list)):
            return parsed
    return None


def _latest_asset_pack(project_id: str) -> dict | None:
    asset_packs = list_asset_packs(project_id=project_id)
    if not asset_packs:
        return None
    return sorted(
        asset_packs,
        key=lambda asset_pack: str(asset_pack.get("created_at") or ""),
        reverse=True,
    )[0]


def _launch_plan_context(project_id: str) -> str:
    launch_plan = get_latest_launch_plan(project_id)
    if launch_plan is None:
        return "No launch plan available."
    return "\n".join(
        [
            f"Launch headline: {str(launch_plan.get('headline') or '').strip()}",
            (
                "Ideal customer profile: "
                f"{str(launch_plan.get('ideal_customer_profile') or '').strip()}"
            ),
            (
                "Painful problem statement: "
                f"{str(launch_plan.get('painful_problem_statement') or '').strip()}"
            ),
            f"Offer summary: {str(launch_plan.get('offer_summary') or '').strip()}",
        ]
    ).strip()


def _asset_pack_context(project_id: str) -> str:
    asset_pack = _latest_asset_pack(project_id)
    if asset_pack is None:
        return "No asset pack available."
    return "\n".join(
        [
            f"Asset headline: {str(asset_pack.get('headline') or '').strip()}",
            f"One sentence pitch: {str(asset_pack.get('one_sentence_pitch') or '').strip()}",
            f"Pilot offer: {str(asset_pack.get('pilot_offer') or '').strip()}",
        ]
    ).strip()


def _fallback_candidate(index: int, project_id: str, target: str, mode: str) -> dict:
    example_companies = [
        "Example Revenue Signal Co",
        "Example Pipeline Insight Partners",
        "Example Forecast Ops Studio",
        "Example GTM Feedback Labs",
        "Example Closed-Lost Learning Group",
        "Example Buyer Insight Systems",
        "Example Revenue Review Collective",
        "Example Deal Quality Advisors",
        "Example Win-Loss Research Works",
        "Example Sales Learning Partners",
    ]
    example_titles = [
        "VP Revenue Operations",
        "Head of Sales Operations",
        "Founder",
        "Chief Revenue Officer",
        "Director of Revenue Strategy",
        "VP Sales",
        "Head of GTM",
        "Revenue Operations Lead",
        "Sales Enablement Director",
        "VP Customer Insights",
    ]
    company_name = example_companies[(index - 1) % len(example_companies)]
    contact_title = example_titles[(index - 1) % len(example_titles)]
    return {
        "project_id": project_id,
        "company_name": f"{company_name} {index}",
        "contact_name": None,
        "contact_title": contact_title,
        "contact_email": None,
        "company_description": (
            "Example candidate generated without live external lead data. "
            "Represents a SaaS-facing revenue team that could fit win-loss analysis outreach."
        ),
        "industry": "B2B SaaS",
        "website": None,
        "linkedin_url": None,
        "lead_source": f"fallback_example:{mode}:no_external_data",
        "fit_reason": (
            f"Example candidate aligned to target '{target}'. "
            "Requires manual operator review before import or outreach."
        ),
        "confidence_score": max(1, min(10, 8 - ((index - 1) % 3))),
        "status": "discovered",
    }


def _fallback_candidates(project_id: str, target: str, count: int, mode: str) -> list[dict]:
    return [_fallback_candidate(index + 1, project_id, target, mode) for index in range(count)]


def _normalize_candidate(candidate: dict, project_id: str, mode: str) -> dict:
    lead_source = f"openai_{mode}_candidate:no_external_verification"
    return {
        "project_id": project_id,
        "company_name": str(candidate.get("company_name") or "").strip() or "Unnamed candidate",
        # No connected source verifies a named person here, so keep the role hypothesis only.
        "contact_name": None,
        "contact_title": (
            str(candidate.get("contact_title")).strip() or None
            if candidate.get("contact_title") is not None
            else None
        ),
        # No verified data source is connected here, so emails remain unverified.
        "contact_email": None,
        "company_description": (
            str(candidate.get("company_description")).strip() or None
            if candidate.get("company_description") is not None
            else None
        ),
        "industry": (
            str(candidate.get("industry")).strip() or None
            if candidate.get("industry") is not None
            else None
        ),
        "website": None,
        "linkedin_url": None,
        "lead_source": lead_source,
        "fit_reason": (
            str(candidate.get("fit_reason") or "").strip()
            or "Candidate appears directionally aligned but still requires operator review."
        ),
        "confidence_score": candidate.get("confidence_score", 5),
        "status": "discovered",
    }


def _discover_with_openai(project_id: str, target: str, count: int, mode: str) -> list[dict] | None:
    prompt = (
        "You are helping an operator build a review queue of candidate B2B leads.\n"
        "Return valid JSON only with a top-level key 'candidates' containing exactly "
        f"{count} items.\n"
        "Every candidate must include these keys: company_name, contact_name, contact_title, "
        "contact_email, company_description, industry, website, linkedin_url, lead_source, "
        "fit_reason, confidence_score.\n"
        "Rules:\n"
        "- Do not claim any private email is verified.\n"
        "- If a direct email is not confidently known from public company-level information, set contact_email to null.\n"
        "- Prefer company-level information and role hypotheses suitable for manual research.\n"
        "- Keep fit_reason specific to why the company fits the target and current offer.\n"
        "- Confidence score must be an integer from 1 to 10.\n"
        "- These are candidates requiring operator review before import or outreach.\n\n"
        f"Discovery mode: {mode}\n"
        f"Target: {target}\n\n"
        f"{_launch_plan_context(project_id)}\n\n"
        f"{_asset_pack_context(project_id)}\n"
    )
    raw_output = generate_openai_text(prompt)
    if not raw_output:
        return None
    parsed = _extract_json_payload(raw_output)
    if isinstance(parsed, dict):
        candidates = parsed.get("candidates")
        if isinstance(candidates, list):
            return [_normalize_candidate(candidate, project_id, mode) for candidate in candidates[:count]]
    if isinstance(parsed, list):
        return [_normalize_candidate(candidate, project_id, mode) for candidate in parsed[:count]]
    return None


def discover_candidate_leads(
    project_id: str,
    target: str,
    count: int,
    mode: str = "manual_research",
) -> list[dict]:
    discovered = _discover_with_openai(project_id=project_id, target=target, count=count, mode=mode)
    if not discovered:
        discovered = _fallback_candidates(project_id=project_id, target=target, count=count, mode=mode)
    if len(discovered) < count:
        discovered.extend(
            _fallback_candidates(
                project_id=project_id,
                target=target,
                count=count - len(discovered),
                mode=mode,
            )
        )

    saved_candidates = []
    for candidate in discovered[:count]:
        saved_candidates.append(create_candidate_lead(candidate))
    return saved_candidates
