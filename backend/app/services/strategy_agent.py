from app.services.prompt_templates import get_mode_prompt
from app.services.research_agent import (
    _clamp_score,
    _extract_json_payload,
    ensure_opportunity_count,
    generate_openai_text,
    get_fallback_profile,
    is_openai_configured,
    normalize_opportunity,
    sort_opportunities,
)


def normalize_strategy_output(
    payload: dict | None,
    objective: str,
    mode: str,
    research_result: dict,
    num_opportunities: int,
) -> dict:
    fallback = get_fallback_profile(mode)
    payload = payload or {}
    payload_opportunities = payload.get("opportunities")
    if not isinstance(payload_opportunities, list):
        payload_opportunities = research_result.get("opportunities", [])

    research_opportunities = research_result.get("opportunities", [])
    normalized_opportunities = []
    for index in range(min(len(payload_opportunities), num_opportunities)):
        fallback_item = research_opportunities[min(index, len(research_opportunities) - 1)]
        normalized_opportunities.append(
            normalize_opportunity(payload_opportunities[index], fallback_item)
        )
    normalized_opportunities = ensure_opportunity_count(
        mode,
        normalized_opportunities,
        num_opportunities,
    )
    normalized_opportunities = sort_opportunities(normalized_opportunities)
    best = normalized_opportunities[0]
    return {
        "offer": str(payload.get("offer") or best["offer"] or fallback["offer"]),
        "mvp": str(payload.get("mvp") or best["mvp"] or fallback["mvp"]),
        "distribution_channel": str(
            payload.get("distribution_channel") or best["distribution_channel"] or fallback["distribution_channel"]
        ),
        "monetization_model": str(
            payload.get("monetization_model") or best["monetization_model"] or fallback["monetization_model"]
        ),
        "strategy_summary": str(
            payload.get("strategy_summary")
            or f"Fallback strategy summary for '{objective}': {fallback['reasoning']}"
        ),
        "opportunity_score": _clamp_score(
            payload.get("opportunity_score") or best["opportunity_score"],
            best["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            payload.get("confidence_score") or best["confidence_score"],
            best["confidence_score"],
        ),
        "opportunities": normalized_opportunities,
    }


def generate_strategy_summary(
    objective: str,
    research_result: dict,
    mode: str = "research_operator",
    num_opportunities: int = 3,
) -> dict:
    fallback = get_fallback_profile(mode)
    if not is_openai_configured():
        return normalize_strategy_output(
            {
                "strategy_summary": (
                    "OpenAI not configured; fallback mode was used. "
                    f"Strategy summary for '{objective}': {fallback['reasoning']}"
                ),
                "opportunities": research_result.get("opportunities", [])[:num_opportunities],
            },
            objective=objective,
            mode=mode,
            research_result=research_result,
            num_opportunities=num_opportunities,
        )

    mode_prompt = get_mode_prompt(mode)
    prompt = (
        f"You are a {mode_prompt['label']} converting research into a commercially strong MVP.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "strategy_summary, opportunities\n"
        f"Refine exactly {num_opportunities} opportunities.\n"
        "Each opportunity must include: title, niche, target_customer, core_problem, offer, mvp, distribution_channel, "
        "monetization_model, opportunity_score, confidence_score, reasoning, next_actions.\n"
        "Scores must be integers from 1 to 10.\n"
        "Keep the recommendations practical and specific.\n\n"
        f"Objective: {objective}\n\n"
        f"Research input:\n{research_result}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_strategy_output(
            _extract_json_payload(openai_output) if isinstance(_extract_json_payload(openai_output), dict) else None,
            objective=objective,
            mode=mode,
            research_result=research_result,
            num_opportunities=num_opportunities,
        )

    return normalize_strategy_output(
        {
            "strategy_summary": (
                "OpenAI request failed; fallback mode was used. "
                f"Strategy summary for '{objective}': {fallback['reasoning']}"
            ),
            "opportunities": research_result.get("opportunities", [])[:num_opportunities],
        },
        objective=objective,
        mode=mode,
        research_result=research_result,
        num_opportunities=num_opportunities,
    )
