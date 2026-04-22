from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.memory_service import create_project, get_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project_endpoint(project: ProjectCreate) -> ProjectResponse:
    created_project = create_project(name=project.name, goal=project.goal)
    return ProjectResponse(**created_project.to_dict())


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_endpoint(project_id: str) -> ProjectResponse:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(**project.to_dict())
