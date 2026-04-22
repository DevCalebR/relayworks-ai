from dataclasses import asdict, dataclass


@dataclass
class RunResult:
    project_id: str
    objective: str
    research_summary: str
    strategy_summary: str
    execution_output: str
    status: str = "completed"

    def to_dict(self) -> dict:
        return asdict(self)
