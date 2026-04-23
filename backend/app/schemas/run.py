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
    research_summary: str
    strategy_summary: str
    execution_output: str
    status: str
    created_at: str
