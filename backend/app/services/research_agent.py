from openai import OpenAI

from app.config import settings


def get_openai_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_research_summary(objective: str) -> str:
    _client = get_openai_client()
    cleaned_objective = objective.strip() or "No objective provided"
    return (
        f"Research summary for '{cleaned_objective}': focus on a narrow business problem, "
        "validate demand with a small target market, and prioritize workflows that show clear ROI."
    )
