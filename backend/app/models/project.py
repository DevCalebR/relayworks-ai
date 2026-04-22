from dataclasses import asdict, dataclass


@dataclass
class Project:
    id: str
    name: str
    goal: str
    status: str = "created"

    def to_dict(self) -> dict:
        return asdict(self)
