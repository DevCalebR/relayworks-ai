from dataclasses import asdict, dataclass


@dataclass
class RunResult:
    id: str
    project_id: str
    objective: str
    research_summary: str
    strategy_summary: str
    execution_output: str
    status: str = "completed"
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
