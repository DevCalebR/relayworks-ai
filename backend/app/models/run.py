from dataclasses import asdict, dataclass


DEFAULT_MODE = "research_operator"


@dataclass
class RunResult:
    id: str
    project_id: str
    objective: str
    research_summary: str = ""
    strategy_summary: str = ""
    execution_output: str = ""
    mode: str = DEFAULT_MODE
    niche: str = "General AI operator opportunity"
    target_customer: str = "Small and midsize businesses"
    core_problem: str = "Teams lack a profitable AI workflow with clear ROI"
    offer: str = "AI operator strategy package"
    mvp: str = "Service-assisted AI workflow MVP"
    distribution_channel: str = "Founder-led outbound"
    monetization_model: str = "Monthly retainer"
    opportunity_score: int = 5
    confidence_score: int = 5
    reasoning: str = "Baseline structured opportunity record."
    next_actions: list[str] | None = None
    status: str = "completed"
    created_at: str = ""

    def to_dict(self) -> dict:
        payload = asdict(self)
        if payload["next_actions"] is None:
            payload["next_actions"] = []
        return payload
