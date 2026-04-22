import json
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.models.project import Project
from app.models.run import RunResult

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(settings.DATA_DIR)
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR

PROJECTS_FILE = DATA_DIR / "projects.json"
RUNS_FILE = DATA_DIR / "runs.json"


def _write_json_file(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def _ensure_json_file(path: Path) -> None:
    if not path.exists():
        _write_json_file(path, [])


def _load_json_file(path: Path) -> list[dict]:
    _ensure_json_file(path)
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raw_data = []
        _write_json_file(path, raw_data)

    if not isinstance(raw_data, list):
        raw_data = []
        _write_json_file(path, raw_data)

    return raw_data


def load_projects() -> list[dict]:
    return _load_json_file(PROJECTS_FILE)


def save_projects(projects: list[dict]) -> None:
    _write_json_file(PROJECTS_FILE, projects)


def create_project(name: str, goal: str) -> Project:
    projects = load_projects()
    project = Project(
        id=f"proj_{uuid4().hex[:12]}",
        name=name,
        goal=goal,
        status="created",
    )
    projects.append(project.to_dict())
    save_projects(projects)
    return project


def get_project(project_id: str) -> Project | None:
    for project_data in load_projects():
        if project_data.get("id") == project_id:
            return Project(**project_data)
    return None


def load_runs() -> list[dict]:
    return _load_json_file(RUNS_FILE)


def save_runs(runs: list[dict]) -> None:
    _write_json_file(RUNS_FILE, runs)


def create_run_record(run_data: dict) -> RunResult:
    runs = load_runs()
    run_record = RunResult(**run_data)
    runs.append(run_record.to_dict())
    save_runs(runs)
    return run_record


def list_runs(project_id: str | None = None) -> list[dict]:
    runs = load_runs()
    if project_id is None:
        return runs
    return [run for run in runs if run.get("project_id") == project_id]
