from uuid import uuid4

from app.models.project import Project

PROJECTS: dict[str, Project] = {}


def create_project(name: str, goal: str) -> Project:
    project = Project(
        id=f"proj_{uuid4().hex[:12]}",
        name=name,
        goal=goal,
        status="created",
    )
    PROJECTS[project.id] = project
    return project


def get_project(project_id: str) -> Project | None:
    return PROJECTS.get(project_id)
