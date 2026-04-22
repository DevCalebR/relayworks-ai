from app.models.run import RunResult
from app.services.execution_agent import generate_execution_output
from app.services.research_agent import generate_research_summary
from app.services.strategy_agent import generate_strategy_summary


def run_agents(project_id: str, objective: str) -> dict:
    research_summary = generate_research_summary(objective)
    strategy_summary = generate_strategy_summary(objective, research_summary)
    execution_output = generate_execution_output(strategy_summary)
    run_result = RunResult(
        project_id=project_id,
        objective=objective,
        research_summary=research_summary,
        strategy_summary=strategy_summary,
        execution_output=execution_output,
        status="completed",
    )
    return run_result.to_dict()
