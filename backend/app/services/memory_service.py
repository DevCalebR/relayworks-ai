import json
from datetime import datetime, timezone
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
LAUNCH_PLANS_FILE = DATA_DIR / "launch_plans.json"
ASSET_PACKS_FILE = DATA_DIR / "asset_packs.json"
LEADS_FILE = DATA_DIR / "leads.json"
OUTREACH_LOGS_FILE = DATA_DIR / "outreach_logs.json"


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def get_run_record(run_id: str, project_id: str | None = None) -> dict | None:
    for run in list_runs(project_id=project_id):
        if run.get("id") == run_id:
            return run
    return None


def load_launch_plans() -> list[dict]:
    return _load_json_file(LAUNCH_PLANS_FILE)


def save_launch_plans(launch_plans: list[dict]) -> None:
    _write_json_file(LAUNCH_PLANS_FILE, launch_plans)


def create_launch_plan_record(launch_plan_data: dict) -> dict:
    launch_plans = load_launch_plans()
    record = {
        **launch_plan_data,
        "id": str(launch_plan_data.get("id") or f"lp_{uuid4().hex[:12]}"),
    }
    launch_plans.append(record)
    save_launch_plans(launch_plans)
    return record


def list_launch_plans(project_id: str | None = None, run_id: str | None = None) -> list[dict]:
    launch_plans = load_launch_plans()
    if project_id is not None:
        launch_plans = [
            launch_plan for launch_plan in launch_plans if launch_plan.get("project_id") == project_id
        ]
    if run_id is not None:
        launch_plans = [
            launch_plan
            for launch_plan in launch_plans
            if launch_plan.get("source_run_id") == run_id
        ]
    return launch_plans


def get_launch_plan_record(launch_plan_id: str, project_id: str | None = None) -> dict | None:
    for launch_plan in list_launch_plans(project_id=project_id):
        if launch_plan.get("id") == launch_plan_id:
            return launch_plan
    return None


def get_latest_launch_plan(project_id: str) -> dict | None:
    launch_plans = list_launch_plans(project_id=project_id)
    if not launch_plans:
        return None
    return sorted(
        launch_plans,
        key=lambda launch_plan: str(launch_plan.get("created_at") or ""),
        reverse=True,
    )[0]


def resolve_stored_launch_plan(
    project_id: str,
    launch_plan_id: str | None = None,
    use_latest_launch_plan: bool = False,
) -> dict | None:
    if launch_plan_id is not None:
        return get_launch_plan_record(launch_plan_id=launch_plan_id, project_id=project_id)

    if use_latest_launch_plan:
        return get_latest_launch_plan(project_id=project_id)

    return None


def load_asset_packs() -> list[dict]:
    return _load_json_file(ASSET_PACKS_FILE)


def save_asset_packs(asset_packs: list[dict]) -> None:
    _write_json_file(ASSET_PACKS_FILE, asset_packs)


def create_asset_pack_record(asset_pack_data: dict) -> dict:
    asset_packs = load_asset_packs()
    record = {
        **asset_pack_data,
        "id": str(asset_pack_data.get("id") or f"asset_{uuid4().hex[:12]}"),
    }
    asset_packs.append(record)
    save_asset_packs(asset_packs)
    return record


def list_asset_packs(
    project_id: str | None = None,
    launch_plan_id: str | None = None,
) -> list[dict]:
    asset_packs = load_asset_packs()
    if project_id is not None:
        asset_packs = [
            asset_pack for asset_pack in asset_packs if asset_pack.get("project_id") == project_id
        ]
    if launch_plan_id is not None:
        asset_packs = [
            asset_pack
            for asset_pack in asset_packs
            if asset_pack.get("launch_plan_id") == launch_plan_id
        ]
    return asset_packs


def get_asset_pack_record(asset_pack_id: str, project_id: str | None = None) -> dict | None:
    for asset_pack in list_asset_packs(project_id=project_id):
        if asset_pack.get("id") == asset_pack_id:
            return asset_pack
    return None


def load_leads() -> list[dict]:
    return _load_json_file(LEADS_FILE)


def save_leads(leads: list[dict]) -> None:
    _write_json_file(LEADS_FILE, leads)


def create_lead(lead_data: dict) -> dict:
    leads = load_leads()
    record = {
        "id": str(lead_data.get("id") or f"lead_{uuid4().hex[:12]}"),
        "project_id": str(lead_data.get("project_id") or ""),
        "company_name": str(lead_data.get("company_name") or ""),
        "contact_name": str(lead_data.get("contact_name") or ""),
        "contact_email": str(lead_data.get("contact_email") or ""),
        "status": str(lead_data.get("status") or "new"),
        "created_at": str(lead_data.get("created_at") or _now_iso()),
    }
    leads.append(record)
    save_leads(leads)
    return record


def list_leads(project_id: str | None = None) -> list[dict]:
    leads = load_leads()
    if project_id is None:
        return leads
    return [lead for lead in leads if lead.get("project_id") == project_id]


def get_lead_record(lead_id: str, project_id: str | None = None) -> dict | None:
    for lead in list_leads(project_id=project_id):
        if lead.get("id") == lead_id:
            return lead
    return None


def update_lead_status(lead_id: str, status: str) -> dict | None:
    leads = load_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["status"] = status
            save_leads(leads)
            return lead
    return None


def load_outreach_logs() -> list[dict]:
    return _load_json_file(OUTREACH_LOGS_FILE)


def save_outreach_logs(outreach_logs: list[dict]) -> None:
    _write_json_file(OUTREACH_LOGS_FILE, outreach_logs)


def create_outreach_log(outreach_log_data: dict) -> dict:
    outreach_logs = load_outreach_logs()
    record = {
        "id": str(outreach_log_data.get("id") or f"outreach_{uuid4().hex[:12]}"),
        "project_id": str(outreach_log_data.get("project_id") or ""),
        "lead_id": str(outreach_log_data.get("lead_id") or ""),
        "asset_pack_id": str(outreach_log_data.get("asset_pack_id") or ""),
        "channel": str(outreach_log_data.get("channel") or "email"),
        "message": str(outreach_log_data.get("message") or ""),
        "status": str(outreach_log_data.get("status") or "sent"),
        "reply_text": (
            str(outreach_log_data.get("reply_text")).strip()
            if outreach_log_data.get("reply_text") is not None
            else None
        ),
        "created_at": str(outreach_log_data.get("created_at") or _now_iso()),
    }
    outreach_logs.append(record)
    save_outreach_logs(outreach_logs)
    return record


def get_outreach_log_record(outreach_id: str) -> dict | None:
    for outreach_log in load_outreach_logs():
        if outreach_log.get("id") == outreach_id:
            return outreach_log
    return None


def update_outreach_status(
    outreach_id: str,
    status: str,
    reply_text: str | None = None,
) -> dict | None:
    outreach_logs = load_outreach_logs()
    for outreach_log in outreach_logs:
        if outreach_log.get("id") == outreach_id:
            outreach_log["status"] = status
            if reply_text is not None:
                outreach_log["reply_text"] = reply_text.strip() or None
            save_outreach_logs(outreach_logs)
            return outreach_log
    return None


def list_outreach_logs(
    project_id: str | None = None,
    lead_id: str | None = None,
) -> list[dict]:
    outreach_logs = load_outreach_logs()
    if project_id is not None:
        outreach_logs = [
            outreach_log
            for outreach_log in outreach_logs
            if outreach_log.get("project_id") == project_id
        ]
    if lead_id is not None:
        outreach_logs = [
            outreach_log for outreach_log in outreach_logs if outreach_log.get("lead_id") == lead_id
        ]
    return outreach_logs


def get_latest_outreach_by_lead(project_id: str) -> dict[str, dict]:
    latest_by_lead: dict[str, dict] = {}
    outreach_logs = sorted(
        list_outreach_logs(project_id=project_id),
        key=lambda outreach_log: (
            str(outreach_log.get("created_at") or ""),
            str(outreach_log.get("id") or ""),
        ),
    )
    for outreach_log in outreach_logs:
        lead_id = str(outreach_log.get("lead_id") or "")
        if lead_id:
            latest_by_lead[lead_id] = outreach_log
    return latest_by_lead


def get_latest_outreach_record(project_id: str, lead_id: str) -> dict | None:
    outreach_logs = sorted(
        list_outreach_logs(project_id=project_id, lead_id=lead_id),
        key=lambda outreach_log: (
            str(outreach_log.get("created_at") or ""),
            str(outreach_log.get("id") or ""),
        ),
    )
    if not outreach_logs:
        return None
    return outreach_logs[-1]


def get_pipeline_metrics(project_id: str) -> dict:
    leads = list_leads(project_id=project_id)
    outreach_logs = list_outreach_logs(project_id=project_id)

    lead_counts = {
        "new": 0,
        "contacted": 0,
        "replied": 0,
        "interested": 0,
        "closed": 0,
        "total": len(leads),
    }
    for lead in leads:
        status = str(lead.get("status") or "")
        if status in lead_counts:
            lead_counts[status] += 1

    outreach_counts = {
        "sent": 0,
        "replied": 0,
        "ignored": 0,
        "total": len(outreach_logs),
    }
    for outreach_log in outreach_logs:
        status = str(outreach_log.get("status") or "")
        if status in outreach_counts:
            outreach_counts[status] += 1

    return {
        "project_id": project_id,
        "lead_counts": lead_counts,
        "outreach_counts": outreach_counts,
    }


def list_follow_up_queue(project_id: str) -> list[dict]:
    leads = list_leads(project_id=project_id)
    latest_by_lead = get_latest_outreach_by_lead(project_id=project_id)
    follow_ups = []

    for lead in leads:
        if str(lead.get("status") or "") != "contacted":
            continue

        lead_id = str(lead.get("id") or "")
        latest_outreach = latest_by_lead.get(lead_id)
        if latest_outreach is None:
            continue
        if str(latest_outreach.get("status") or "") != "sent":
            continue

        follow_ups.append(
            {
                "lead_id": lead_id,
                "company_name": str(lead.get("company_name") or ""),
                "contact_name": str(lead.get("contact_name") or ""),
                "last_outreach_id": str(latest_outreach.get("id") or ""),
                "channel": str(latest_outreach.get("channel") or ""),
                "message": str(latest_outreach.get("message") or ""),
            }
        )

    return follow_ups


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


def resolve_run_opportunity(project_id: str, run_id: str) -> dict | None:
    run = get_run_record(run_id=run_id, project_id=project_id)
    if run is None:
        return None
    return {
        "project_id": project_id,
        "source_run_id": run["id"],
        "mode": run["mode"],
        "objective": run["objective"],
        "selected_opportunity": run["best_opportunity"],
    }


def resolve_launch_plan_source(
    project_id: str,
    run_id: str | None = None,
    mode: str | None = None,
    use_top_opportunity: bool = False,
) -> dict | None:
    if run_id is not None:
        return resolve_run_opportunity(project_id=project_id, run_id=run_id)

    if not use_top_opportunity:
        return None

    compare_result = compare_best_runs(project_id=project_id, mode=mode)
    top_opportunity = compare_result.get("top_opportunity")
    if not isinstance(top_opportunity, dict) or not top_opportunity:
        return None

    source_run_id = str(top_opportunity.get("run_id") or "")
    if not source_run_id:
        return None
    return resolve_run_opportunity(project_id=project_id, run_id=source_run_id)


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
