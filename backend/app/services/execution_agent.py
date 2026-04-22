from app.services.research_agent import generate_openai_text, is_openai_configured


def generate_execution_output(strategy_summary: str, objective: str) -> str:
    if not is_openai_configured():
        return (
            "OpenAI not configured; fallback mode was used. "
            "Execution output: define the MVP scope, write the first operator workflow, prepare a landing "
            "page outline, and schedule customer discovery calls. "
            f"Strategy input: {strategy_summary}"
        )

    prompt = (
        "You are an execution operator preparing the first implementation sprint for an AI MVP.\n"
        "Produce a concise action plan with:\n"
        "1. concrete execution plan\n"
        "2. first deliverables\n"
        "3. suggested next actions\n"
        "Keep it plain text and immediately actionable.\n\n"
        f"Objective: {objective}\n\n"
        f"Strategy summary:\n{strategy_summary}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        return openai_output

    return (
        "OpenAI request failed; fallback mode was used. "
        "Execution output: draft the MVP scope, define the first user journey, and prepare the "
        f"next implementation steps based on this plan. Strategy input: {strategy_summary}"
    )
