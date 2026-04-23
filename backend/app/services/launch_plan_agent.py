import json
from datetime import datetime, timezone

from app.services.research_agent import _extract_json_payload, generate_openai_text


def _normalize_text(value: object, fallback: str) -> str:
    if isinstance(value, list):
        text = "; ".join(str(item).strip() for item in value if str(item).strip())
    elif isinstance(value, dict):
        text = ""
    else:
        text = str(value or "").strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                text = "; ".join(str(item).strip() for item in parsed if str(item).strip())
    return text or fallback


def _normalize_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return [item for item in fallback if item]
    normalized = [str(item).strip() for item in value if str(item).strip()]
    return normalized or [item for item in fallback if item]


def _build_fallback_launch_plan(
    project_id: str,
    source_run_id: str,
    mode: str,
    selected_opportunity: dict,
) -> dict:
    title = selected_opportunity["title"]
    target_customer = selected_opportunity["target_customer"]
    problem = selected_opportunity["core_problem"]
    offer = selected_opportunity["offer"]
    mvp = selected_opportunity["mvp"]
    pricing = selected_opportunity["monetization_model"]
    distribution_channel = selected_opportunity["distribution_channel"]

    acquisition_channels = [
        channel.strip(" .")
        for channel in distribution_channel.replace(" and ", ",").split(",")
        if channel.strip(" .")
    ]
    if not acquisition_channels:
        acquisition_channels = ["Founder-led outbound", "Warm referrals", "Targeted LinkedIn outreach"]

    return {
        "project_id": project_id,
        "source_run_id": source_run_id,
        "mode": mode,
        "selected_opportunity": selected_opportunity,
        "headline": f"{title} for {target_customer}",
        "ideal_customer_profile": (
            f"{target_customer} with a visible budget and an urgent need to solve: {problem}"
        ),
        "painful_problem_statement": problem,
        "offer_summary": offer,
        "mvp_scope": [
            f"Deliver the narrowest paid pilot around: {mvp}",
            "Set up a lightweight onboarding and reporting workflow.",
            "Ship one repeatable weekly deliverable that proves ROI quickly.",
        ],
        "pricing_hypothesis": pricing,
        "acquisition_channels": acquisition_channels,
        "sales_motion": (
            "Run direct outreach to a tightly filtered list, pitch a paid pilot, and close 2 to 3 "
            "design partners before adding product complexity."
        ),
        "first_30_day_plan": [
            "Week 1: define the pilot package, ICP list, and outreach assets.",
            "Week 2: contact 30 qualified prospects and book discovery calls.",
            "Week 3: onboard the first pilot customer and deliver the initial workflow manually.",
            "Week 4: convert pilot feedback into a sharper offer and a repeatable case study.",
        ],
        "success_metrics": [
            "At least 10 qualified conversations with target buyers.",
            "2 or more paid pilot customers within 30 days.",
            "A clear ROI signal or repeat usage pattern from pilot accounts.",
        ],
        "biggest_risks": [
            "The pain is real but not urgent enough to trigger a purchase now.",
            "Manual delivery takes too much effort before repeatability is proven.",
            "Positioning is too broad to convert quickly in outbound.",
        ],
        "mitigation_steps": [
            "Narrow the offer to one painful use case and one buyer profile.",
            "Run the first pilots manually to learn before automating more workflow.",
            "Use weekly feedback loops to tighten messaging and pricing after each sales call.",
        ],
        "launch_recommendation": (
            "Launch immediately as a service-led paid pilot, keep the scope narrow, and only "
            "productize the workflow after 2 to 3 customers validate recurring demand."
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_launch_plan_output(
    payload: dict | None,
    project_id: str,
    source_run_id: str,
    mode: str,
    selected_opportunity: dict,
) -> dict:
    fallback = _build_fallback_launch_plan(
        project_id=project_id,
        source_run_id=source_run_id,
        mode=mode,
        selected_opportunity=selected_opportunity,
    )
    payload = payload or {}

    return {
        "project_id": project_id,
        "source_run_id": source_run_id,
        "mode": mode,
        "selected_opportunity": selected_opportunity,
        "headline": _normalize_text(payload.get("headline"), fallback["headline"]),
        "ideal_customer_profile": _normalize_text(
            payload.get("ideal_customer_profile"),
            fallback["ideal_customer_profile"],
        ),
        "painful_problem_statement": _normalize_text(
            payload.get("painful_problem_statement"),
            fallback["painful_problem_statement"],
        ),
        "offer_summary": _normalize_text(payload.get("offer_summary"), fallback["offer_summary"]),
        "mvp_scope": _normalize_list(payload.get("mvp_scope"), fallback["mvp_scope"]),
        "pricing_hypothesis": _normalize_text(
            payload.get("pricing_hypothesis"),
            fallback["pricing_hypothesis"],
        ),
        "acquisition_channels": _normalize_list(
            payload.get("acquisition_channels"),
            fallback["acquisition_channels"],
        ),
        "sales_motion": _normalize_text(payload.get("sales_motion"), fallback["sales_motion"]),
        "first_30_day_plan": _normalize_list(
            payload.get("first_30_day_plan"),
            fallback["first_30_day_plan"],
        ),
        "success_metrics": _normalize_list(
            payload.get("success_metrics"),
            fallback["success_metrics"],
        ),
        "biggest_risks": _normalize_list(
            payload.get("biggest_risks"),
            fallback["biggest_risks"],
        ),
        "mitigation_steps": _normalize_list(
            payload.get("mitigation_steps"),
            fallback["mitigation_steps"],
        ),
        "launch_recommendation": _normalize_text(
            payload.get("launch_recommendation"),
            fallback["launch_recommendation"],
        ),
        "created_at": _normalize_text(payload.get("created_at"), fallback["created_at"]),
    }


def generate_launch_plan(
    project_id: str,
    source_run_id: str,
    mode: str,
    selected_opportunity: dict,
    objective: str,
) -> tuple[dict, str]:
    prompt = (
        "You are a practical startup operator turning a validated business opportunity into a launch plan.\n"
        "Return valid JSON only with these keys:\n"
        "headline, ideal_customer_profile, painful_problem_statement, offer_summary, mvp_scope, "
        "pricing_hypothesis, acquisition_channels, sales_motion, first_30_day_plan, success_metrics, "
        "biggest_risks, mitigation_steps, launch_recommendation\n"
        "All list fields must be short non-empty arrays. Keep the output concise, concrete, and commercially useful.\n\n"
        f"Project objective: {objective}\n"
        f"Source mode: {mode}\n"
        f"Selected opportunity:\n{selected_opportunity}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        payload = _extract_json_payload(openai_output)
        if isinstance(payload, dict):
            return (
                _normalize_launch_plan_output(
                    payload=payload,
                    project_id=project_id,
                    source_run_id=source_run_id,
                    mode=mode,
                    selected_opportunity=selected_opportunity,
                ),
                "openai",
            )

    return (
        _normalize_launch_plan_output(
            payload=None,
            project_id=project_id,
            source_run_id=source_run_id,
            mode=mode,
            selected_opportunity=selected_opportunity,
        ),
        "fallback",
    )
