import json

from openai import OpenAI

from app.config import settings
from app.services.prompt_templates import get_fallback_opportunities, get_mode_prompt


def is_openai_configured() -> bool:
    api_key = settings.OPENAI_API_KEY.strip()
    return bool(api_key and api_key != "your_openai_key_here")


def get_openai_client() -> OpenAI | None:
    if not is_openai_configured():
        return None
    try:
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        return None


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


def _clamp_score(value: int | str | None, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(10, parsed))


def get_fallback_profile(mode: str) -> dict:
    return get_mode_prompt(mode)["fallback"]


def normalize_next_actions(value: list | None, fallback_actions: list[str]) -> list[str]:
    if not isinstance(value, list):
        return [str(action) for action in fallback_actions]
    normalized = [str(action).strip() for action in value if str(action).strip()]
    return normalized or [str(action) for action in fallback_actions]


def normalize_opportunity(payload: dict | None, fallback: dict) -> dict:
    payload = payload or {}
    return {
        "title": str(payload.get("title") or fallback["title"]),
        "niche": str(payload.get("niche") or fallback["niche"]),
        "target_customer": str(payload.get("target_customer") or fallback["target_customer"]),
        "core_problem": str(payload.get("core_problem") or fallback["core_problem"]),
        "offer": str(payload.get("offer") or fallback["offer"]),
        "mvp": str(payload.get("mvp") or fallback["mvp"]),
        "distribution_channel": str(
            payload.get("distribution_channel") or fallback["distribution_channel"]
        ),
        "monetization_model": str(
            payload.get("monetization_model") or fallback["monetization_model"]
        ),
        "opportunity_score": _clamp_score(
            payload.get("opportunity_score"),
            fallback["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            payload.get("confidence_score"),
            fallback["confidence_score"],
        ),
        "reasoning": str(payload.get("reasoning") or fallback["reasoning"]),
        "next_actions": normalize_next_actions(
            payload.get("next_actions"),
            fallback["next_actions"],
        ),
    }


def sort_opportunities(opportunities: list[dict]) -> list[dict]:
    return sorted(
        opportunities,
        key=lambda item: (
            -int(item["opportunity_score"]),
            -int(item["confidence_score"]),
        ),
    )


def ensure_opportunity_count(mode: str, opportunities: list[dict], count: int) -> list[dict]:
    fallback_items = get_fallback_opportunities(mode, max(count, 5))
    normalized = list(opportunities[:count])
    index = 0
    while len(normalized) < count and index < len(fallback_items):
        normalized.append(normalize_opportunity(fallback_items[index], fallback_items[index]))
        index += 1
    return normalized[:count]


def normalize_research_output(
    payload: dict | None,
    objective: str,
    mode: str,
    num_opportunities: int,
) -> dict:
    fallback = get_fallback_profile(mode)
    fallback_items = get_fallback_opportunities(mode, max(num_opportunities, 5))
    payload = payload or {}
    cleaned_objective = objective.strip() or "No objective provided"
    payload_opportunities = payload.get("opportunities")
    if not isinstance(payload_opportunities, list):
        payload_opportunities = []
    normalized_opportunities = []
    for index in range(min(len(payload_opportunities), num_opportunities)):
        fallback_item = fallback_items[min(index, len(fallback_items) - 1)]
        normalized_opportunities.append(
            normalize_opportunity(payload_opportunities[index], fallback_item)
        )
    normalized_opportunities = ensure_opportunity_count(
        mode,
        normalized_opportunities,
        num_opportunities,
    )
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
        "opportunities": normalized_opportunities,
    }


def generate_research_summary(
    objective: str,
    mode: str = "research_operator",
    num_opportunities: int = 3,
) -> dict:
    cleaned_objective = objective.strip() or "No objective provided"
    mode_prompt = get_mode_prompt(mode)
    fallback = get_fallback_profile(mode)
    fallback_opportunities = get_fallback_opportunities(mode, max(num_opportunities, 5))

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
                "opportunities": fallback_opportunities[:num_opportunities],
            },
            objective=cleaned_objective,
            mode=mode,
            num_opportunities=num_opportunities,
        )

    prompt = (
        f"You are a {mode_prompt['label']} analyzing profitable AI business opportunities.\n"
        f"Mode guidance: {mode_prompt['guidance']}\n"
        "Return valid JSON only with these keys:\n"
        "research_summary, reasoning, opportunities\n"
        f"Generate exactly {num_opportunities} opportunities.\n"
        "Each opportunity must include: title, niche, target_customer, core_problem, offer, mvp, "
        "distribution_channel, monetization_model, opportunity_score, confidence_score, reasoning, next_actions.\n"
        "Scores must be integers from 1 to 10 and next_actions must be a short non-empty array.\n"
        "Keep every field concise, practical, and commercially grounded.\n\n"
        f"Objective: {cleaned_objective}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return normalize_research_output(
            _extract_json_payload(openai_output) if isinstance(_extract_json_payload(openai_output), dict) else None,
            objective=cleaned_objective,
            mode=mode,
            num_opportunities=num_opportunities,
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
            "opportunities": fallback_opportunities[:num_opportunities],
        },
        objective=cleaned_objective,
        mode=mode,
        num_opportunities=num_opportunities,
    )
