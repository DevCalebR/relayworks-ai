from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    goal: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    goal: str
    status: str
