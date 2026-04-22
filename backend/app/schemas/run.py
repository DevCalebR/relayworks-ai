from pydantic import BaseModel


class RunRequest(BaseModel):
    project_id: str
    objective: str


class RunResponse(BaseModel):
    project_id: str
    objective: str
    research_summary: str
    strategy_summary: str
    execution_output: str
    status: str
