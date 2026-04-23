from app.services.prompt_templates import get_mode_prompt
from app.services.research_agent import (
    _clamp_score,
    _extract_json_object,
    generate_openai_text,
    get_fallback_profile,
    is_openai_configured,
)


def normalize_strategy_output(payload: dict | None, objective: str, mode: str) -> dict:
    fallback = get_fallback_profile(mode)
    payload = payload or {}
    return {
        "offer": str(payload.get("offer") or fallback["offer"]),
        "mvp": str(payload.get("mvp") or fallback["mvp"]),
        "distribution_channel": str(
            payload.get("distribution_channel") or fallback["distribution_channel"]
        ),
        "monetization_model": str(
            payload.get("monetization_model") or fallback["monetization_model"]
        ),
        "strategy_summary": str(
            payload.get("strategy_summary")
            or f"Fallback strategy summary for '{objective}': {fallback['reasoning']}"
        ),
        "opportunity_score": _clamp_score(
            payload.get("opportunity_score"),
            fallback["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            payload.get("confidence_score"),
            fallback["confidence_score"],
        ),
    }


def generate_strategy_summary(objective: str, research_result: dict, mode: str = "research_operator") -> dict:
    fallback = get_fallback_profile(mode)
    if not is_openai_configured():
        return normalize_strategy_output(
            {
                "offer": fallback["offer"],
                "mvp": fallback["mvp"],
                "distribution_channel": fallback["distribution_channel"],
                "monetization_model": fallback["monetization_model"],
                "strategy_summary": (
                    "OpenAI not configured; fallback mode was used. "
                    f"Strategy summary for '{objective}': {fallback['reasoning']}"
                ),
                "opportunity_score": fallback["opportunity_score"],
                "confidence_score": fallback["confidence_score"],
            },
            objective=objective,
            mode=mode,
        )

    mode_prompt = get_mode_prompt(mode)
    prompt = (
        f"You are a {mode_prompt['label']} converting research into a commercially strong MVP.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "offer, mvp, distribution_channel, monetization_model, strategy_summary, opportunity_score, confidence_score\n"
        "Scores must be integers from 1 to 10.\n"
        "Keep the recommendations practical and specific.\n\n"
        f"Objective: {objective}\n\n"
        f"Research input:\n{research_result}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_strategy_output(
            _extract_json_object(openai_output),
            objective=objective,
            mode=mode,
        )

    return normalize_strategy_output(
        {
            "offer": fallback["offer"],
            "mvp": fallback["mvp"],
            "distribution_channel": fallback["distribution_channel"],
            "monetization_model": fallback["monetization_model"],
            "strategy_summary": (
                "OpenAI request failed; fallback mode was used. "
                f"Strategy summary for '{objective}': {fallback['reasoning']}"
            ),
            "opportunity_score": fallback["opportunity_score"],
            "confidence_score": fallback["confidence_score"],
        },
        objective=objective,
        mode=mode,
    )
