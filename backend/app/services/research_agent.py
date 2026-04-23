import json

from openai import OpenAI

from app.config import settings
from app.services.prompt_templates import get_mode_prompt


def is_openai_configured() -> bool:
    api_key = settings.OPENAI_API_KEY.strip()
    return bool(api_key and api_key != "your_openai_key_here")


def get_openai_client() -> OpenAI | None:
    if not is_openai_configured():
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_openai_text(prompt: str) -> str | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
        )
    except Exception:
        return None

    output_text = getattr(response, "output_text", "")
    if isinstance(output_text, str):
        cleaned_output = output_text.strip()
        if cleaned_output:
            return cleaned_output
    return None


def _extract_json_object(raw_text: str) -> dict | None:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _clamp_score(value: int | str | None, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(10, parsed))


def get_fallback_profile(mode: str) -> dict:
    return get_mode_prompt(mode)["fallback"]


def normalize_research_output(payload: dict | None, objective: str, mode: str) -> dict:
    fallback = get_fallback_profile(mode)
    payload = payload or {}
    cleaned_objective = objective.strip() or "No objective provided"
    return {
        "mode": mode,
        "niche": str(payload.get("niche") or fallback["niche"]),
        "target_customer": str(payload.get("target_customer") or fallback["target_customer"]),
        "core_problem": str(payload.get("core_problem") or fallback["core_problem"]),
        "research_summary": str(
            payload.get("research_summary")
            or f"Fallback research summary for '{cleaned_objective}': {fallback['reasoning']}"
        ),
        "reasoning": str(payload.get("reasoning") or fallback["reasoning"]),
    }


def generate_research_summary(objective: str, mode: str = "research_operator") -> dict:
    cleaned_objective = objective.strip() or "No objective provided"
    mode_prompt = get_mode_prompt(mode)
    fallback = get_fallback_profile(mode)

    if not is_openai_configured():
        return normalize_research_output(
            {
                "niche": fallback["niche"],
                "target_customer": fallback["target_customer"],
                "core_problem": fallback["core_problem"],
                "research_summary": (
                    "OpenAI not configured; fallback mode was used. "
                    f"Research summary for '{cleaned_objective}': {fallback['reasoning']}"
                ),
                "reasoning": fallback["reasoning"],
            },
            objective=cleaned_objective,
            mode=mode,
        )

    prompt = (
        f"You are a {mode_prompt['label']} analyzing profitable AI business opportunities.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "niche, target_customer, core_problem, research_summary, reasoning\n"
        "Keep every field concise, practical, and commercially grounded.\n\n"
        f"Objective: {cleaned_objective}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_research_output(
            _extract_json_object(openai_output),
            objective=cleaned_objective,
            mode=mode,
        )

    return normalize_research_output(
        {
            "niche": fallback["niche"],
            "target_customer": fallback["target_customer"],
            "core_problem": fallback["core_problem"],
            "research_summary": (
                "OpenAI request failed; fallback mode was used. "
                f"Research summary for '{cleaned_objective}': {fallback['reasoning']}"
            ),
            "reasoning": fallback["reasoning"],
        },
        objective=cleaned_objective,
        mode=mode,
    )
