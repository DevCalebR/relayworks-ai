from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import RunResult
from app.services.execution_agent import generate_execution_output
from app.services.memory_service import create_run_record
from app.services.research_agent import sort_opportunities, generate_research_summary
from app.services.strategy_agent import generate_strategy_summary


def run_agents(
    project_id: str,
    objective: str,
    mode: str = "research_operator",
    num_opportunities: int = 3,
) -> dict:
    research_result = generate_research_summary(
        objective,
        mode=mode,
        num_opportunities=num_opportunities,
    )
    strategy_result = generate_strategy_summary(
        objective,
        research_result,
        mode=mode,
        num_opportunities=num_opportunities,
    )
    ranked_opportunities = sort_opportunities(strategy_result["opportunities"])[:num_opportunities]
    execution_result = generate_execution_output(ranked_opportunities, objective, mode=mode)
    ranked_opportunities[0] = execution_result["best_opportunity"]
    best_opportunity = ranked_opportunities[0]
    run_result = RunResult(
        id=f"run_{uuid4().hex[:12]}",
        project_id=project_id,
        objective=objective,
        mode=mode,
        title=best_opportunity["title"],
        niche=best_opportunity["niche"],
        target_customer=best_opportunity["target_customer"],
        core_problem=best_opportunity["core_problem"],
        offer=best_opportunity["offer"],
        mvp=best_opportunity["mvp"],
        distribution_channel=best_opportunity["distribution_channel"],
        monetization_model=best_opportunity["monetization_model"],
        opportunity_score=best_opportunity["opportunity_score"],
        confidence_score=best_opportunity["confidence_score"],
        reasoning=best_opportunity["reasoning"],
        next_actions=best_opportunity["next_actions"],
        opportunities=ranked_opportunities,
        best_opportunity=best_opportunity,
        research_summary=research_result["research_summary"],
        strategy_summary=strategy_result["strategy_summary"],
        execution_output=execution_result["execution_output"],
        status="completed",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    saved_run = create_run_record(run_result.to_dict())
    return saved_run.to_dict()
