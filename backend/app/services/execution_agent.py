from app.services.prompt_templates import get_mode_prompt
from app.services.research_agent import (
    _extract_json_object,
    generate_openai_text,
    get_fallback_profile,
    is_openai_configured,
)


def normalize_execution_output(payload: dict | None, strategy_result: dict, mode: str) -> dict:
    fallback = get_fallback_profile(mode)
    payload = payload or {}
    next_actions = payload.get("next_actions")
    if not isinstance(next_actions, list) or not next_actions:
        next_actions = fallback["next_actions"]
    normalized_actions = [str(action) for action in next_actions[:5]]
    return {
        "execution_output": str(
            payload.get("execution_output")
            or "Fallback execution output: prioritize early validation, draft the first deliverables, "
            f"and use this plan to launch quickly. Strategy input: {strategy_result}"
        ),
        "next_actions": normalized_actions,
    }


def generate_execution_output(
    strategy_result: dict,
    objective: str,
    mode: str = "research_operator",
) -> dict:
    fallback = get_fallback_profile(mode)
    if not is_openai_configured():
        deliverables = ", ".join(fallback["deliverables"])
        return normalize_execution_output(
            {
                "execution_output": (
                    "OpenAI not configured; fallback mode was used. "
                    "Execution output: launch the first version around a narrow paid pilot, ship the first "
                    f"deliverables ({deliverables}), and use founder-led sales to validate demand. "
                    f"Strategy input: {strategy_result}"
                ),
                "next_actions": fallback["next_actions"],
            },
            strategy_result=strategy_result,
            mode=mode,
        )

    mode_prompt = get_mode_prompt(mode)
    prompt = (
        f"You are a {mode_prompt['label']} preparing an execution plan for a commercial MVP.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "execution_output, next_actions\n"
        "The execution_output should include a concrete plan, first deliverables, and suggested next actions.\n"
        "next_actions must be a short array of actionable strings.\n\n"
        f"Objective: {objective}\n\n"
        f"Strategy input:\n{strategy_result}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_execution_output(
            _extract_json_object(openai_output),
            strategy_result=strategy_result,
            mode=mode,
        )

    deliverables = ", ".join(fallback["deliverables"])
    return normalize_execution_output(
        {
            "execution_output": (
                "OpenAI request failed; fallback mode was used. "
                "Execution output: define the MVP scope, assemble the first deliverables "
                f"({deliverables}), and execute a fast validation sprint. Strategy input: {strategy_result}"
            ),
            "next_actions": fallback["next_actions"],
        },
        strategy_result=strategy_result,
        mode=mode,
    )
