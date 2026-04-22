from fastapi import APIRouter

from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.memory_service import create_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project_endpoint(project: ProjectCreate) -> ProjectResponse:
    created_project = create_project(name=project.name, goal=project.goal)
    return ProjectResponse(**created_project.to_dict())
