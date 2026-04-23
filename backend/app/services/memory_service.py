import json
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.models.project import Project
from app.models.run import DEFAULT_MODE, RunResult
from app.services.prompt_templates import OPERATOR_MODES, get_fallback_opportunities, get_mode_prompt
from app.services.research_agent import sort_opportunities

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


def compare_best_runs(project_id: str, mode: str | None = None) -> dict:
    runs = list_runs(project_id=project_id)
    if mode is not None:
        runs = [run for run in runs if run.get("mode") == mode]

    ranked_opportunities = [
        {
            **run["best_opportunity"],
            "run_id": run["id"],
            "mode": run["mode"],
            "created_at": run["created_at"],
        }
        for run in runs
        if isinstance(run.get("best_opportunity"), dict) and run["best_opportunity"]
    ]
    ranked_opportunities = sort_opportunities(ranked_opportunities)

    if not ranked_opportunities:
        message = (
            f"No runs found for project '{project_id}' and mode '{mode}'."
            if mode is not None
            else f"No runs found for project '{project_id}'."
        )
    else:
        message = None

    return {
        "project_id": project_id,
        "total_runs": len(runs),
        "total_opportunities": len(ranked_opportunities),
        "message": message,
        "top_opportunity": ranked_opportunities[0] if ranked_opportunities else None,
        "ranked_opportunities": ranked_opportunities,
    }


def normalize_run_record(run_data: dict) -> dict:
    requested_mode = str(run_data.get("mode") or DEFAULT_MODE)
    mode = requested_mode if requested_mode in OPERATOR_MODES else DEFAULT_MODE
    fallback = get_mode_prompt(mode)["fallback"]
    fallback_opportunities = get_fallback_opportunities(mode, 5)
    next_actions = run_data.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = fallback["next_actions"]

    raw_opportunities = run_data.get("opportunities")
    if not isinstance(raw_opportunities, list) or not raw_opportunities:
        raw_opportunities = [
            {
                "title": str(run_data.get("title") or fallback_opportunities[0]["title"]),
                "niche": str(run_data.get("niche") or fallback["niche"]),
                "target_customer": str(
                    run_data.get("target_customer") or fallback["target_customer"]
                ),
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
            }
        ]

    normalized_opportunities = []
    for index, opportunity in enumerate(raw_opportunities):
        fallback_item = fallback_opportunities[min(index, len(fallback_opportunities) - 1)]
        normalized_opportunities.append(_normalize_opportunity_record(opportunity, fallback_item))

    normalized_opportunities = sort_opportunities(normalized_opportunities)

    raw_best = run_data.get("best_opportunity")
    if isinstance(raw_best, dict) and raw_best:
        best_fallback = normalized_opportunities[0]
        best_opportunity = _normalize_opportunity_record(raw_best, best_fallback)
    else:
        best_opportunity = normalized_opportunities[0]

    normalized_opportunities[0] = best_opportunity

    normalized = {
        "id": str(run_data.get("id") or f"run_{uuid4().hex[:12]}"),
        "project_id": str(run_data.get("project_id") or ""),
        "objective": str(run_data.get("objective") or ""),
        "mode": mode,
        "title": str(run_data.get("title") or best_opportunity["title"]),
        "niche": str(run_data.get("niche") or best_opportunity["niche"]),
        "target_customer": str(
            run_data.get("target_customer") or best_opportunity["target_customer"]
        ),
        "core_problem": str(run_data.get("core_problem") or best_opportunity["core_problem"]),
        "offer": str(run_data.get("offer") or best_opportunity["offer"]),
        "mvp": str(run_data.get("mvp") or best_opportunity["mvp"]),
        "distribution_channel": str(
            run_data.get("distribution_channel") or best_opportunity["distribution_channel"]
        ),
        "monetization_model": str(
            run_data.get("monetization_model") or best_opportunity["monetization_model"]
        ),
        "opportunity_score": _clamp_score(
            run_data.get("opportunity_score") or best_opportunity["opportunity_score"],
            best_opportunity["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            run_data.get("confidence_score") or best_opportunity["confidence_score"],
            best_opportunity["confidence_score"],
        ),
        "reasoning": str(run_data.get("reasoning") or best_opportunity["reasoning"]),
        "next_actions": [
            str(action)
            for action in (
                run_data.get("next_actions")
                if isinstance(run_data.get("next_actions"), list)
                else best_opportunity["next_actions"]
            )[:5]
        ],
        "opportunities": normalized_opportunities,
        "best_opportunity": best_opportunity,
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


def _normalize_opportunity_record(opportunity: dict, fallback: dict) -> dict:
    next_actions = opportunity.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = fallback["next_actions"]
    normalized = {
        "title": str(opportunity.get("title") or fallback["title"]),
        "niche": str(opportunity.get("niche") or fallback["niche"]),
        "target_customer": str(
            opportunity.get("target_customer") or fallback["target_customer"]
        ),
        "core_problem": str(opportunity.get("core_problem") or fallback["core_problem"]),
        "offer": str(opportunity.get("offer") or fallback["offer"]),
        "mvp": str(opportunity.get("mvp") or fallback["mvp"]),
        "distribution_channel": str(
            opportunity.get("distribution_channel") or fallback["distribution_channel"]
        ),
        "monetization_model": str(
            opportunity.get("monetization_model") or fallback["monetization_model"]
        ),
        "opportunity_score": _clamp_score(
            opportunity.get("opportunity_score"),
            fallback["opportunity_score"],
        ),
        "confidence_score": _clamp_score(
            opportunity.get("confidence_score"),
            fallback["confidence_score"],
        ),
        "reasoning": str(opportunity.get("reasoning") or fallback["reasoning"]),
        "next_actions": [str(action) for action in next_actions[:5]],
    }
    return normalized


def _clamp_score(value: int | str | None, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(10, parsed))
