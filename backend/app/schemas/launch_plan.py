from pydantic import BaseModel

from app.schemas.run import Opportunity, OperatorMode


class LaunchPlanRequest(BaseModel):
    project_id: str
    run_id: str | None = None
    mode: OperatorMode | None = None
    use_top_opportunity: bool = False


class LaunchPlanResponse(BaseModel):
    project_id: str
    source_run_id: str
    mode: OperatorMode = "research_operator"
    selected_opportunity: Opportunity
    headline: str
    ideal_customer_profile: str
    painful_problem_statement: str
    offer_summary: str
    mvp_scope: list[str]
    pricing_hypothesis: str
    acquisition_channels: list[str]
    sales_motion: str
    first_30_day_plan: list[str]
    success_metrics: list[str]
    biggest_risks: list[str]
    mitigation_steps: list[str]
    launch_recommendation: str
    created_at: str
