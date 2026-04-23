from app.services.prompt_templates import get_mode_prompt
from app.services.research_agent import (
    _extract_json_payload,
    generate_openai_text,
    get_fallback_profile,
    is_openai_configured,
    normalize_opportunity,
)


def normalize_execution_output(
    payload: dict | None,
    strategy_result: dict,
    mode: str,
    best_opportunity: dict,
) -> dict:
    fallback = get_fallback_profile(mode)
    payload = payload or {}
    payload_best = payload.get("best_opportunity")
    if not isinstance(payload_best, dict):
        payload_best = {}
    next_actions = payload.get("next_actions")
    if not isinstance(next_actions, list) or not next_actions:
        next_actions = payload_best.get("next_actions")
    normalized_best = normalize_opportunity(
        {**best_opportunity, **payload_best, "next_actions": next_actions},
        best_opportunity,
    )
    return {
        "execution_output": str(
            payload.get("execution_output")
            or "Fallback execution output: prioritize early validation, draft the first deliverables, "
            f"and use this plan to launch quickly. Strategy input: {strategy_result}"
        ),
        "best_opportunity": normalized_best,
    }


def generate_execution_output(
    opportunities: list[dict],
    objective: str,
    mode: str = "research_operator",
) -> dict:
    fallback = get_fallback_profile(mode)
    best_opportunity = opportunities[0]
    if not is_openai_configured():
        deliverables = ", ".join(fallback["deliverables"])
        return normalize_execution_output(
            {
                "execution_output": (
                    "OpenAI not configured; fallback mode was used. "
                    "Execution output: launch the first version around a narrow paid pilot, ship the first "
                    f"deliverables ({deliverables}), and use founder-led sales to validate demand. "
                    f"Strategy input: {best_opportunity}"
                ),
                "best_opportunity": {
                    **best_opportunity,
                    "next_actions": best_opportunity.get("next_actions") or fallback["next_actions"],
                },
            },
            strategy_result=best_opportunity,
            mode=mode,
            best_opportunity=best_opportunity,
        )

    mode_prompt = get_mode_prompt(mode)
    prompt = (
        f"You are a {mode_prompt['label']} preparing an execution plan for a commercial MVP.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "execution_output, best_opportunity\n"
        "best_opportunity must include: title, niche, target_customer, core_problem, offer, mvp, distribution_channel, "
        "monetization_model, opportunity_score, confidence_score, reasoning, next_actions.\n"
        "Improve the top opportunity with stronger immediate next actions and clearer first deliverables.\n\n"
        f"Objective: {objective}\n\n"
        f"Top opportunity to execute:\n{best_opportunity}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_execution_output(
            _extract_json_payload(openai_output) if isinstance(_extract_json_payload(openai_output), dict) else None,
            strategy_result=best_opportunity,
            mode=mode,
            best_opportunity=best_opportunity,
        )

    deliverables = ", ".join(fallback["deliverables"])
    return normalize_execution_output(
        {
            "execution_output": (
                "OpenAI request failed; fallback mode was used. "
                "Execution output: define the MVP scope, assemble the first deliverables "
                f"({deliverables}), and execute a fast validation sprint. Strategy input: {best_opportunity}"
            ),
            "best_opportunity": {
                **best_opportunity,
                "next_actions": best_opportunity.get("next_actions") or fallback["next_actions"],
            },
        },
        strategy_result=best_opportunity,
        mode=mode,
        best_opportunity=best_opportunity,
    )
