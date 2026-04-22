def generate_strategy_summary(objective: str, research_summary: str) -> str:
    return (
        f"Strategy summary for '{objective}': use the research findings to define one MVP, "
        "target a single customer profile, and ship a lightweight operator workflow first. "
        f"Research input: {research_summary}"
    )
