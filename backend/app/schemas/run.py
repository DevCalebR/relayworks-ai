from typing import Literal

from pydantic import BaseModel, Field

OperatorMode = Literal[
    "research_operator",
    "content_operator",
    "leadgen_operator",
    "product_operator",
]


class RunRequest(BaseModel):
    project_id: str
    objective: str
    mode: OperatorMode = "research_operator"
    num_opportunities: int = Field(default=3, ge=1, le=5)


class Opportunity(BaseModel):
    title: str
    niche: str
    target_customer: str
    core_problem: str
    offer: str
    mvp: str
    distribution_channel: str
    monetization_model: str
    opportunity_score: int = Field(ge=1, le=10)
    confidence_score: int = Field(ge=1, le=10)
    reasoning: str
    next_actions: list[str]


class ComparedOpportunity(Opportunity):
    run_id: str
    mode: OperatorMode = "research_operator"
    created_at: str


class RunResponse(BaseModel):
    id: str
    project_id: str
    objective: str
    mode: OperatorMode = "research_operator"
    niche: str
    target_customer: str
    core_problem: str
    offer: str
    mvp: str
    distribution_channel: str
    monetization_model: str
    opportunity_score: int = Field(ge=1, le=10)
    confidence_score: int = Field(ge=1, le=10)
    reasoning: str
    next_actions: list[str]
    opportunities: list[Opportunity]
    best_opportunity: Opportunity
    research_summary: str
    strategy_summary: str
    execution_output: str
    status: str
    created_at: str


class CompareResponse(BaseModel):
    project_id: str
    total_runs: int
    total_opportunities: int
    message: str | None = None
    top_opportunity: ComparedOpportunity | None = None
    ranked_opportunities: list[ComparedOpportunity]
