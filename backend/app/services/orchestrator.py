from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import RunResult
from app.services.execution_agent import generate_execution_output
from app.services.memory_service import create_run_record
from app.services.research_agent import generate_research_summary
from app.services.strategy_agent import generate_strategy_summary


def run_agents(project_id: str, objective: str) -> dict:
    research_summary = generate_research_summary(objective)
    strategy_summary = generate_strategy_summary(objective, research_summary)
    execution_output = generate_execution_output(strategy_summary, objective)
    run_result = RunResult(
        id=f"run_{uuid4().hex[:12]}",
        project_id=project_id,
        objective=objective,
        research_summary=research_summary,
        strategy_summary=strategy_summary,
        execution_output=execution_output,
        status="completed",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    saved_run = create_run_record(run_result.to_dict())
    return saved_run.to_dict()
