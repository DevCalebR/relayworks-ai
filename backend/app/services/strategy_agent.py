from app.services.research_agent import generate_openai_text, is_openai_configured


def generate_strategy_summary(objective: str, research_summary: str) -> str:
    if not is_openai_configured():
        return (
            "OpenAI not configured; fallback mode was used. "
            f"Strategy summary for '{objective}': target one customer segment, package one repeatable "
            "operator workflow as the MVP, and sell a narrow high-value service before expanding. "
            f"Research input: {research_summary}"
        )

    prompt = (
        "You are a startup strategy operator turning research into a strong MVP plan.\n"
        "Create a concise strategy summary for the objective below.\n"
        "Recommend the best niche, offer shape, MVP scope, and go-to-market focus.\n"
        "Keep it practical and plain text.\n\n"
        f"Objective: {objective}\n\n"
        f"Research summary:\n{research_summary}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return openai_output

    return (
        "OpenAI request failed; fallback mode was used. "
        f"Strategy summary for '{objective}': use the research findings to define one MVP, "
        "target a single customer profile, and ship a lightweight operator workflow first. "
        f"Research input: {research_summary}"
    )
