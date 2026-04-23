from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import RunResult
from app.services.execution_agent import generate_execution_output
from app.services.memory_service import create_run_record
from app.services.research_agent import generate_research_summary
from app.services.strategy_agent import generate_strategy_summary


def run_agents(project_id: str, objective: str, mode: str = "research_operator") -> dict:
    research_result = generate_research_summary(objective, mode=mode)
    strategy_result = generate_strategy_summary(objective, research_result, mode=mode)
    execution_result = generate_execution_output(strategy_result, objective, mode=mode)
    run_result = RunResult(
        id=f"run_{uuid4().hex[:12]}",
        project_id=project_id,
        objective=objective,
        mode=mode,
        niche=research_result["niche"],
        target_customer=research_result["target_customer"],
        core_problem=research_result["core_problem"],
        offer=strategy_result["offer"],
        mvp=strategy_result["mvp"],
        distribution_channel=strategy_result["distribution_channel"],
        monetization_model=strategy_result["monetization_model"],
        opportunity_score=strategy_result["opportunity_score"],
        confidence_score=strategy_result["confidence_score"],
        reasoning=research_result["reasoning"],
        next_actions=execution_result["next_actions"],
        research_summary=research_result["research_summary"],
        strategy_summary=strategy_result["strategy_summary"],
        execution_output=execution_result["execution_output"],
        status="completed",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    saved_run = create_run_record(run_result.to_dict())
    return saved_run.to_dict()
