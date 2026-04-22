from pydantic import BaseModel


class ProjectSchema(BaseModel):
    name: str = ""
    description: str = ""
