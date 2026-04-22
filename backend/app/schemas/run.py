from pydantic import BaseModel


class RunSchema(BaseModel):
    project_id: str = ""
    status: str = "pending"
