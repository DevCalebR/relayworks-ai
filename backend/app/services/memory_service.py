import json
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.models.project import Project
from app.models.run import DEFAULT_MODE, RunResult
from app.services.prompt_templates import OPERATOR_MODES, get_mode_prompt

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
    run_record = RunResult(**normalize_run_record(run_data))
    runs.append(run_record.to_dict())
    save_runs(runs)
    return run_record


def list_runs(project_id: str | None = None) -> list[dict]:
    runs = [normalize_run_record(run) for run in load_runs()]
    if project_id is None:
        return runs
    return [run for run in runs if run.get("project_id") == project_id]


def normalize_run_record(run_data: dict) -> dict:
    requested_mode = str(run_data.get("mode") or DEFAULT_MODE)
    mode = requested_mode if requested_mode in OPERATOR_MODES else DEFAULT_MODE
    fallback = get_mode_prompt(mode)["fallback"]
    next_actions = run_data.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = fallback["next_actions"]

    normalized = {
        "id": str(run_data.get("id") or f"run_{uuid4().hex[:12]}"),
        "project_id": str(run_data.get("project_id") or ""),
        "objective": str(run_data.get("objective") or ""),
        "mode": mode,
        "niche": str(run_data.get("niche") or fallback["niche"]),
        "target_customer": str(run_data.get("target_customer") or fallback["target_customer"]),
        "core_problem": str(run_data.get("core_problem") or fallback["core_problem"]),
        "offer": str(run_data.get("offer") or fallback["offer"]),
        "mvp": str(run_data.get("mvp") or fallback["mvp"]),
        "distribution_channel": str(
            run_data.get("distribution_channel") or fallback["distribution_channel"]
        ),
        "monetization_model": str(
            run_data.get("monetization_model") or fallback["monetization_model"]
        ),
        "opportunity_score": _clamp_score(
            run_data.get("opportunity_score"),
            fallback["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            run_data.get("confidence_score"),
            fallback["confidence_score"],
        ),
        "reasoning": str(run_data.get("reasoning") or fallback["reasoning"]),
        "next_actions": [str(action) for action in next_actions[:5]],
        "research_summary": str(
            run_data.get("research_summary")
            or f"Legacy run normalized into {mode} format."
        ),
        "strategy_summary": str(
            run_data.get("strategy_summary")
            or "Legacy strategy summary preserved with default structured fields."
        ),
        "execution_output": str(
            run_data.get("execution_output")
            or "Legacy execution output preserved with default structured fields."
        ),
        "status": str(run_data.get("status") or "completed"),
        "created_at": str(run_data.get("created_at") or ""),
    }
    return normalized


def _clamp_score(value: int | str | None, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(10, parsed))
