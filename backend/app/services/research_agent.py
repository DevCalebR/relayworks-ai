from openai import OpenAI

from app.config import settings


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


def generate_research_summary(objective: str) -> str:
    cleaned_objective = objective.strip() or "No objective provided"

    if not is_openai_configured():
        return (
            "OpenAI not configured; fallback mode was used. "
            f"Research summary for '{cleaned_objective}': prioritize a niche with urgent workflow pain, "
            "clear budget, and repeatable analyst-style tasks that can be automated quickly."
        )

    prompt = (
        "You are a practical market research operator helping define an AI business.\n"
        "Write a concise research summary for the objective below.\n"
        "Focus on market opportunity, promising niches, customer pain, and commercial signals.\n"
        "Keep it tight, concrete, and plain text.\n\n"
        f"Objective: {cleaned_objective}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return openai_output

    return (
        "OpenAI request failed; fallback mode was used. "
        f"Research summary for '{cleaned_objective}': focus on a narrow business problem, "
        "validate demand with a small target market, and prioritize workflows that show clear ROI."
    )
