import json
from datetime import datetime, timezone

from app.services.research_agent import _extract_json_payload, generate_openai_text


def _normalize_text(value: object, fallback: str) -> str:
    if isinstance(value, list):
        text = " ".join(str(item).strip() for item in value if str(item).strip())
    elif isinstance(value, dict):
        text = ""
    else:
        text = str(value or "").strip()
    return text or fallback


def _normalize_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return list(fallback)
    normalized = [str(item).strip() for item in value if str(item).strip()]
    return normalized or list(fallback)


def _normalize_faq(value: object, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return list(fallback)

    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if question and answer:
            normalized.append({"question": question, "answer": answer})

    return normalized or list(fallback)


def _build_fallback_asset_pack(launch_plan: dict) -> dict:
    selected_opportunity = launch_plan.get("selected_opportunity") or {}
    title = str(selected_opportunity.get("title") or "AI Win-Loss Interview Analyzer")
    target_customer = str(
        selected_opportunity.get("target_customer") or "Seed to Series B SaaS teams"
    )
    problem = str(
        selected_opportunity.get("core_problem")
        or "Revenue teams struggle to turn deal feedback into repeatable pipeline decisions."
    )
    offer = str(
        selected_opportunity.get("offer")
        or "AI-backed win-loss interview research with weekly decision briefs."
    )
    pricing_hypothesis = str(
        launch_plan.get("pricing_hypothesis") or "Monthly retainer with onboarding fee."
    )
    offer_summary = str(launch_plan.get("offer_summary") or offer)
    clean_offer_summary = offer_summary.rstrip(" .")
    clean_problem = problem.rstrip(" .")
    clean_pricing_hypothesis = pricing_hypothesis.rstrip(" .")
    headline = f"Turn lost deals into the next quarter's revenue plays"
    one_sentence_pitch = (
        f"{title} helps {target_customer} capture structured buyer feedback, spot the real "
        "reasons deals stall or churn, and turn those signals into sharper revenue decisions."
    )
    landing_page_hero = "Know why deals are won, lost, or stuck before the quarter slips"
    landing_page_subheadline = (
        f"{clean_offer_summary} for {target_customer} that need practical win-loss insight without "
        "waiting on a full BI project."
    )
    key_benefits = [
        "Surface the top loss reasons, buyer objections, and message gaps across active deals.",
        "Give revenue leaders a weekly brief they can use in pipeline reviews and forecast calls.",
        "Help sales ops turn scattered notes, call summaries, and CRM data into one repeatable signal.",
    ]
    offer_stack = [
        "Win-loss interview analysis across recent closed-lost and stalled deals.",
        "Weekly decision brief with ranked themes, objection patterns, and recommended actions.",
        "Leadership readout tailored for sales, product marketing, and revenue operations.",
    ]
    call_to_action = "Book a 20-minute working session to review three recent lost deals."
    cold_outreach_email_subject = "Quick way to find why deals are slipping"
    cold_outreach_email_body = (
        f"Hi {{first_name}},\n\n"
        f"I help {target_customer} turn call notes, CRM history, and interview feedback into a "
        "weekly win-loss brief that shows why deals are lost, delayed, or discounted.\n\n"
        f"For teams dealing with a familiar problem, {clean_problem.lower()}, the goal is simple: give revenue leaders a "
        "clear view of the patterns they can fix this quarter, without waiting on a heavy analytics project.\n\n"
        "If useful, I can walk you through what the first pilot would cover and the exact output your team would get.\n\n"
        "Open to a short call next week?"
    )
    linkedin_dm = (
        "Working on a practical way for SaaS revenue teams to turn win-loss interviews, call notes, "
        "and CRM context into a weekly brief on why deals are really moving or dying. If this is a "
        "priority for your team, I can share the pilot structure."
    )
    discovery_call_script = [
        "How are you currently learning why deals are won, lost, or slipping late in the cycle?",
        "Where does feedback live today: CRM fields, call notes, Gong summaries, manager reviews, or interviews?",
        "Which decisions would improve fastest if your team had cleaner win-loss signal every week?",
        "How are revenue leadership and sales ops measuring whether messaging or process changes are working?",
        "If we ran a 30-day pilot, what outcome would make it worth expanding?",
    ]
    pilot_offer = (
        "30-day pilot covering one segment of recent closed-lost and late-stage stalled deals, "
        "including interview analysis, weekly decision briefs, and a final leadership readout."
    )
    pricing_blurb = (
        f"Start with a paid pilot tied to a defined deal sample and weekly executive output, then roll "
        f"into {clean_pricing_hypothesis.lower()} once the team wants ongoing coverage."
    )
    faq = [
        {
            "question": "Who is this for?",
            "answer": (
                "Revenue leaders and sales operations teams at Seed to Series B SaaS companies that need a clearer view of why deals are won or lost."
            ),
        },
        {
            "question": "What do we need to provide?",
            "answer": (
                "A small set of recent deals, call notes or summaries, and access to the context your team already uses for pipeline reviews."
            ),
        },
        {
            "question": "What does the pilot produce?",
            "answer": (
                "A weekly brief with ranked themes, buyer objections, loss reasons, and concrete actions for revenue leadership."
            ),
        },
    ]

    return {
        "project_id": str(launch_plan.get("project_id") or ""),
        "launch_plan_id": str(launch_plan.get("id") or ""),
        "source_run_id": str(launch_plan.get("source_run_id") or ""),
        "headline": headline,
        "one_sentence_pitch": one_sentence_pitch,
        "landing_page_hero": landing_page_hero,
        "landing_page_subheadline": landing_page_subheadline,
        "key_benefits": key_benefits,
        "offer_stack": offer_stack,
        "call_to_action": call_to_action,
        "cold_outreach_email_subject": cold_outreach_email_subject,
        "cold_outreach_email_body": cold_outreach_email_body,
        "linkedin_dm": linkedin_dm,
        "discovery_call_script": discovery_call_script,
        "pilot_offer": pilot_offer,
        "pricing_blurb": pricing_blurb,
        "faq": faq,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_asset_pack_output(payload: dict | None, launch_plan: dict) -> dict:
    fallback = _build_fallback_asset_pack(launch_plan)
    payload = payload or {}

    return {
        "project_id": fallback["project_id"],
        "launch_plan_id": fallback["launch_plan_id"],
        "source_run_id": fallback["source_run_id"],
        "headline": _normalize_text(payload.get("headline"), fallback["headline"]),
        "one_sentence_pitch": _normalize_text(
            payload.get("one_sentence_pitch"),
            fallback["one_sentence_pitch"],
        ),
        "landing_page_hero": _normalize_text(
            payload.get("landing_page_hero"),
            fallback["landing_page_hero"],
        ),
        "landing_page_subheadline": _normalize_text(
            payload.get("landing_page_subheadline"),
            fallback["landing_page_subheadline"],
        ),
        "key_benefits": _normalize_list(payload.get("key_benefits"), fallback["key_benefits"]),
        "offer_stack": _normalize_list(payload.get("offer_stack"), fallback["offer_stack"]),
        "call_to_action": _normalize_text(
            payload.get("call_to_action"),
            fallback["call_to_action"],
        ),
        "cold_outreach_email_subject": _normalize_text(
            payload.get("cold_outreach_email_subject"),
            fallback["cold_outreach_email_subject"],
        ),
        "cold_outreach_email_body": _normalize_text(
            payload.get("cold_outreach_email_body"),
            fallback["cold_outreach_email_body"],
        ),
        "linkedin_dm": _normalize_text(payload.get("linkedin_dm"), fallback["linkedin_dm"]),
        "discovery_call_script": _normalize_list(
            payload.get("discovery_call_script"),
            fallback["discovery_call_script"],
        ),
        "pilot_offer": _normalize_text(payload.get("pilot_offer"), fallback["pilot_offer"]),
        "pricing_blurb": _normalize_text(
            payload.get("pricing_blurb"),
            fallback["pricing_blurb"],
        ),
        "faq": _normalize_faq(payload.get("faq"), fallback["faq"]),
        "created_at": _normalize_text(payload.get("created_at"), fallback["created_at"]),
    }


def generate_asset_pack(launch_plan: dict) -> tuple[dict, str]:
    selected_opportunity = launch_plan.get("selected_opportunity") or {}
    prompt = (
        "You are a practical B2B founder-operator creating the first sales and marketing assets for a "
        "validated AI offer.\n"
        "Return valid JSON only with these keys:\n"
        "headline, one_sentence_pitch, landing_page_hero, landing_page_subheadline, key_benefits, "
        "offer_stack, call_to_action, cold_outreach_email_subject, cold_outreach_email_body, "
        "linkedin_dm, discovery_call_script, pilot_offer, pricing_blurb, faq\n"
        "The faq field must be a non-empty array of objects with question and answer.\n"
        "Keep the writing concise, practical, commercially sharp, and suitable for Seed to Series B SaaS "
        "buyers, revenue leaders, and sales operations leaders. Avoid hype.\n"
        "All list fields must be short non-empty arrays.\n\n"
        f"Launch plan: {json.dumps(launch_plan, ensure_ascii=True)}\n"
        f"Selected opportunity: {json.dumps(selected_opportunity, ensure_ascii=True)}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        payload = _extract_json_payload(openai_output)
        if isinstance(payload, dict):
            return _normalize_asset_pack_output(payload, launch_plan), "openai"

    return _normalize_asset_pack_output(None, launch_plan), "fallback"
