#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ID = "proj_952a38d1f320"
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = DATA_DIR / "backups"

FILES_TO_RESET = (
    "projects.json",
    "runs.json",
    "launch_plans.json",
    "asset_packs.json",
    "leads.json",
    "outreach_logs.json",
    "candidate_leads.json",
)


def build_dataset() -> dict[str, list[dict]]:
    best_opportunity = {
        "title": "AI Win-Loss Interview Analyzer",
        "niche": "B2B Revenue Intelligence",
        "target_customer": "Seed to Series B SaaS teams",
        "core_problem": (
            "Revenue teams lose structured deal feedback and cannot quickly isolate churn, "
            "pipeline friction, or the real reasons deals stall."
        ),
        "offer": "AI-backed win-loss interview research with weekly decision briefs.",
        "mvp": (
            "A service-led workflow that ingests call notes, CRM context, and post-deal "
            "interviews to produce ranked loss reasons and buyer-pattern summaries."
        ),
        "distribution_channel": "Founder-led outbound to SaaS revenue leaders.",
        "monetization_model": "Monthly retainer with a paid onboarding sprint.",
        "opportunity_score": 10,
        "confidence_score": 9,
        "reasoning": (
            "The wedge is fast to launch, solves a visible revenue problem, and can start "
            "manually before the workflow is productized."
        ),
        "next_actions": [
            "Interview five SaaS revenue leaders about their current loss-review process.",
            "Package a two-week pilot around closed-lost and stalled deals.",
            "Create a one-page weekly decision brief template.",
            "Gather three sample datasets to refine the first delivery workflow.",
            "Define the metrics that prove revenue insight quality quickly.",
        ],
    }

    secondary_research_opportunity = {
        "title": "AI Objection Pattern Tracker",
        "niche": "Sales Process Intelligence",
        "target_customer": "Series A to Series C SaaS sales teams",
        "core_problem": (
            "Sales leaders hear objections repeatedly but cannot turn them into a repeatable "
            "coaching and messaging system."
        ),
        "offer": "Weekly objection-pattern analysis with coaching recommendations.",
        "mvp": "Manual review of recent calls with a ranked objection brief for managers.",
        "distribution_channel": "Warm outbound through RevOps and sales advisory networks.",
        "monetization_model": "Pilot fee followed by a monthly advisory retainer.",
        "opportunity_score": 8,
        "confidence_score": 7,
        "reasoning": (
            "The pain is clear, but positioning overlaps with broader sales enablement offers."
        ),
        "next_actions": [
            "Validate objection-tracking workflows with three sales managers.",
            "Draft the first manager-facing coaching brief.",
            "Test positioning versus generic sales enablement offers.",
        ],
    }

    content_operator_opportunity = {
        "title": "Regulatory Compliance Content Platform",
        "niche": "Legal and Compliance Content",
        "target_customer": "Small legal teams and compliance operators",
        "core_problem": (
            "Teams need fast, digestible updates on changing regulations but cannot maintain "
            "timely sector-specific content internally."
        ),
        "offer": "AI-assisted regulatory update briefs tailored by industry.",
        "mvp": "A web dashboard with weekly update memos for one industry vertical.",
        "distribution_channel": "Content marketing and targeted email outreach.",
        "monetization_model": "Subscription access with a premium research tier.",
        "opportunity_score": 7,
        "confidence_score": 7,
        "reasoning": (
            "Useful and defensible, but slower to prove immediate revenue impact than the "
            "win-loss service offer."
        ),
        "next_actions": [
            "Choose one vertical with high regulatory churn.",
            "Draft a sample weekly update memo.",
            "Test willingness to pay with three compliance leads.",
        ],
    }

    return {
        "projects.json": [
            {
                "id": PROJECT_ID,
                "name": "RelayWorks Demo Project",
                "goal": "Demo the full local operator workflow from opportunity analysis to follow-up.",
                "status": "created",
            }
        ],
        "runs.json": [
            {
                "id": "run_demo_win_loss",
                "project_id": PROJECT_ID,
                "objective": "Find the best fast-to-market profitable AI operator business opportunity",
                "research_summary": (
                    "Revenue teams repeatedly lose useful win-loss signal because feedback is split "
                    "across calls, CRM notes, and informal post-mortems."
                ),
                "strategy_summary": (
                    "Start with a service-led offer that turns recent lost or stalled deals into a "
                    "weekly decision brief for revenue leadership."
                ),
                "execution_output": json.dumps(
                    {
                        "pilot": "14-day win-loss analysis sprint",
                        "deliverables": [
                            "Ranked loss reasons",
                            "Buyer objection patterns",
                            "Weekly decision brief",
                        ],
                    }
                ),
                "mode": "research_operator",
                "title": best_opportunity["title"],
                "niche": best_opportunity["niche"],
                "target_customer": best_opportunity["target_customer"],
                "core_problem": best_opportunity["core_problem"],
                "offer": best_opportunity["offer"],
                "mvp": best_opportunity["mvp"],
                "distribution_channel": best_opportunity["distribution_channel"],
                "monetization_model": best_opportunity["monetization_model"],
                "opportunity_score": best_opportunity["opportunity_score"],
                "confidence_score": best_opportunity["confidence_score"],
                "reasoning": best_opportunity["reasoning"],
                "next_actions": best_opportunity["next_actions"],
                "opportunities": [
                    best_opportunity,
                    secondary_research_opportunity,
                ],
                "best_opportunity": best_opportunity,
                "status": "completed",
                "created_at": "2026-04-26T13:00:00+00:00",
            },
            {
                "id": "run_demo_compliance_content",
                "project_id": PROJECT_ID,
                "objective": "Compare a content-led operator opportunity against the current top idea",
                "research_summary": (
                    "Compliance teams want concise regulatory updates, but the purchase motion is "
                    "typically slower and less urgent than revenue tooling."
                ),
                "strategy_summary": (
                    "Position the offer as recurring vertical research, but keep it secondary to the "
                    "win-loss analyzer for demos."
                ),
                "execution_output": json.dumps(
                    {
                        "pilot": "Weekly compliance digest",
                        "deliverables": [
                            "Sector summary",
                            "Action checklist",
                            "Client-facing memo",
                        ],
                    }
                ),
                "mode": "content_operator",
                "title": content_operator_opportunity["title"],
                "niche": content_operator_opportunity["niche"],
                "target_customer": content_operator_opportunity["target_customer"],
                "core_problem": content_operator_opportunity["core_problem"],
                "offer": content_operator_opportunity["offer"],
                "mvp": content_operator_opportunity["mvp"],
                "distribution_channel": content_operator_opportunity["distribution_channel"],
                "monetization_model": content_operator_opportunity["monetization_model"],
                "opportunity_score": content_operator_opportunity["opportunity_score"],
                "confidence_score": content_operator_opportunity["confidence_score"],
                "reasoning": content_operator_opportunity["reasoning"],
                "next_actions": content_operator_opportunity["next_actions"],
                "opportunities": [content_operator_opportunity],
                "best_opportunity": content_operator_opportunity,
                "status": "completed",
                "created_at": "2026-04-26T12:20:00+00:00",
            },
        ],
        "launch_plans.json": [
            {
                "id": "launch_plan_demo_win_loss",
                "project_id": PROJECT_ID,
                "source_run_id": "run_demo_win_loss",
                "mode": "research_operator",
                "selected_opportunity": best_opportunity,
                "headline": "AI Win-Loss Interview Analyzer for revenue teams that need fast clarity",
                "ideal_customer_profile": (
                    "Seed to Series B SaaS teams with active outbound or mid-market sales motions, "
                    "a RevOps owner, and recurring questions about why deals slip or churn."
                ),
                "painful_problem_statement": best_opportunity["core_problem"],
                "offer_summary": (
                    "A service-led pilot that turns recent closed-lost and stalled deals into a "
                    "weekly decision brief for revenue leadership."
                ),
                "mvp_scope": [
                    "Review 15 to 20 recent lost or stalled deals.",
                    "Normalize notes, call summaries, and CRM context into one analysis workflow.",
                    "Deliver a weekly brief with ranked loss reasons and recommended fixes.",
                ],
                "pricing_hypothesis": "$3,500 onboarding sprint followed by a $2,000 monthly retainer.",
                "acquisition_channels": [
                    "Founder-led outbound to RevOps and sales leaders",
                    "Warm intros through revenue advisory operators",
                ],
                "sales_motion": (
                    "Sell a tight paid pilot, show a concrete weekly brief, and expand only after "
                    "the first customer validates recurring insight demand."
                ),
                "first_30_day_plan": [
                    "Week 1: finalize pilot scope, sample brief, and target-account list.",
                    "Week 2: run 25 focused outbound touches and book discovery calls.",
                    "Week 3: onboard one pilot customer and deliver the first brief manually.",
                    "Week 4: tighten offer language from live objections and results.",
                ],
                "success_metrics": [
                    "At least 5 qualified revenue conversations.",
                    "1 paid pilot within the first month.",
                    "A repeatable weekly brief that leadership actually uses.",
                ],
                "biggest_risks": [
                    "Prospects may frame the problem as nice-to-have research.",
                    "Manual delivery could stay messy without a narrow scope.",
                    "The offer can drift into generic RevOps consulting if messaging is loose.",
                ],
                "mitigation_steps": [
                    "Anchor every pitch to one painful revenue decision the brief improves.",
                    "Keep the first pilot constrained to a single segment and deal sample.",
                    "Show exact report output early so the offer feels concrete.",
                ],
                "launch_recommendation": (
                    "Run the offer immediately as a narrow paid pilot and use the first customer "
                    "delivery to harden the workflow before deeper automation."
                ),
                "created_at": "2026-04-26T13:10:00+00:00",
                "generation_mode": "demo_seed",
            }
        ],
        "asset_packs.json": [
            {
                "id": "asset_pack_demo_win_loss",
                "project_id": PROJECT_ID,
                "launch_plan_id": "launch_plan_demo_win_loss",
                "source_run_id": "run_demo_win_loss",
                "headline": "Turn lost deals into next quarter's revenue plays",
                "one_sentence_pitch": (
                    "RelayWorks helps SaaS revenue teams convert scattered deal feedback into a "
                    "weekly win-loss brief that shows why opportunities slip, stall, or churn."
                ),
                "landing_page_hero": "Know why deals are dying before the quarter slips away",
                "landing_page_subheadline": (
                    "AI-backed win-loss interview analysis for Seed to Series B SaaS teams that "
                    "need practical revenue insight without waiting on a full BI project."
                ),
                "key_benefits": [
                    "Rank the real loss reasons hiding across CRM notes and call summaries.",
                    "Give revenue leadership one weekly brief they can use in forecast reviews.",
                    "Turn scattered buyer feedback into concrete fixes for messaging and process.",
                ],
                "offer_stack": [
                    "Analysis of recent closed-lost and stalled deals",
                    "Weekly decision brief with themes, objections, and actions",
                    "Leadership readout for RevOps, sales, and product marketing",
                ],
                "call_to_action": "Book a 20-minute working session on three recent lost deals.",
                "cold_outreach_email_subject": "Quick way to find why deals are slipping",
                "cold_outreach_email_body": (
                    "Hi {first_name},\n\n"
                    "I help SaaS revenue teams turn call notes, CRM context, and post-deal feedback "
                    "into a weekly win-loss brief that shows why deals are lost, delayed, or discounted.\n\n"
                    "If your team is trying to tighten forecasts, messaging, or pipeline reviews "
                    "without a heavyweight analytics project, I can share the exact pilot structure "
                    "and sample output.\n\n"
                    "Open to a short call next week?"
                ),
                "linkedin_dm": (
                    "Working on a practical win-loss analysis offer for SaaS revenue teams that need "
                    "clean signal on why deals are really moving or dying. Happy to share the pilot "
                    "structure if this is on your radar."
                ),
                "discovery_call_script": [
                    "How are you currently learning why deals are won, lost, or delayed?",
                    "Where does that feedback live today?",
                    "Which revenue decisions would improve fastest with cleaner signal?",
                    "How do leaders review objections and loss patterns right now?",
                    "What outcome would make a 30-day pilot obviously worthwhile?",
                ],
                "pilot_offer": (
                    "A 30-day pilot covering one segment of recent lost and stalled deals, including "
                    "analysis, weekly decision briefs, and a final leadership readout."
                ),
                "pricing_blurb": (
                    "Start with a paid onboarding sprint tied to a defined deal sample, then roll "
                    "into a monthly retainer once the brief becomes part of the team's cadence."
                ),
                "faq": [
                    {
                        "question": "Who is this for?",
                        "answer": (
                            "Revenue leaders and RevOps teams at Seed to Series B SaaS companies "
                            "that need a clearer view of why deals are won or lost."
                        ),
                    },
                    {
                        "question": "What does the pilot require?",
                        "answer": (
                            "A small sample of recent deals, call notes or summaries, and the context "
                            "your team already uses for pipeline reviews."
                        ),
                    },
                    {
                        "question": "What comes out of the pilot?",
                        "answer": (
                            "A weekly brief with ranked themes, buyer objections, loss reasons, and "
                            "recommended next actions."
                        ),
                    },
                ],
                "created_at": "2026-04-26T13:20:00+00:00",
                "generation_mode": "demo_seed",
            }
        ],
        "candidate_leads.json": [
            {
                "id": "candidate_demo_001",
                "project_id": PROJECT_ID,
                "company_name": "ChurnCheck",
                "contact_name": None,
                "contact_title": "Head of Revenue",
                "contact_email": None,
                "company_description": (
                    "ChurnCheck helps B2B SaaS operators understand account health and retention risk."
                ),
                "industry": "SaaS",
                "website": "https://churncheck.example",
                "linkedin_url": "https://www.linkedin.com/company/churncheck-example",
                "lead_source": "demo_seed:manual_research",
                "fit_reason": (
                    "Their team already works close to retention data, so a win-loss brief is an easy "
                    "adjacent revenue insight offer."
                ),
                "confidence_score": 8,
                "status": "discovered",
                "created_at": "2026-04-26T13:25:00+00:00",
            },
            {
                "id": "candidate_demo_002",
                "project_id": PROJECT_ID,
                "company_name": "SignalLoop Revenue",
                "contact_name": "Ethan Carter",
                "contact_title": "VP of Revenue Operations",
                "contact_email": "ethan@signalloop.example",
                "company_description": (
                    "SignalLoop Revenue helps SaaS teams improve pipeline visibility and sales execution."
                ),
                "industry": "Revenue operations consulting",
                "website": "https://signalloop.example",
                "linkedin_url": "https://www.linkedin.com/company/signalloop-revenue",
                "lead_source": "demo_seed:manual_research",
                "fit_reason": (
                    "They already advise on pipeline performance, so win-loss analysis is a strong "
                    "conversation starter and a plausible pilot buyer."
                ),
                "confidence_score": 9,
                "status": "imported",
                "created_at": "2026-04-26T13:15:00+00:00",
            },
            {
                "id": "candidate_demo_003",
                "project_id": PROJECT_ID,
                "company_name": "Compliance Beacon",
                "contact_name": None,
                "contact_title": "Compliance Program Manager",
                "contact_email": None,
                "company_description": (
                    "Compliance Beacon delivers sector-specific regulatory summaries for legal teams."
                ),
                "industry": "Legal technology",
                "website": "https://compliancebeacon.example",
                "linkedin_url": None,
                "lead_source": "demo_seed:manual_research",
                "fit_reason": (
                    "Useful operator business, but it is weaker for the current demo because the pain "
                    "is less urgent than revenue decision support."
                ),
                "confidence_score": 6,
                "status": "rejected",
                "created_at": "2026-04-26T12:40:00+00:00",
            },
        ],
        "leads.json": [
            {
                "id": "lead_demo_001",
                "project_id": PROJECT_ID,
                "company_name": "Atlas Growth Systems",
                "contact_name": "Maya Chen",
                "contact_email": "maya@atlasgrowth.example",
                "status": "new",
                "company_description": (
                    "Atlas Growth Systems advises SaaS teams on revenue process and forecast discipline."
                ),
                "industry": "Revenue growth advisory",
                "website": "https://atlasgrowth.example",
                "notes": "Interested in tighter lost-deal learning loops before board reviews.",
                "created_at": "2026-04-26T13:32:00+00:00",
            },
            {
                "id": "lead_demo_002",
                "project_id": PROJECT_ID,
                "company_name": "Beacon Revenue Ops",
                "contact_name": "Jon Patel",
                "contact_email": "jon@beaconrevops.example",
                "status": "new",
                "company_description": (
                    "Beacon Revenue Ops helps SaaS companies audit pipeline health and sales process."
                ),
                "industry": "Revenue operations consulting",
                "website": "https://beaconrevops.example",
                "notes": "Could be a good fit for a pilot around stalled enterprise deals.",
                "created_at": "2026-04-26T13:28:00+00:00",
            },
            {
                "id": "lead_demo_003",
                "project_id": PROJECT_ID,
                "company_name": "Pipeline Harbor",
                "contact_name": "Jordan Lee",
                "contact_email": "jordan@pipelineharbor.example",
                "status": "contacted",
                "company_description": (
                    "Pipeline Harbor supports early-stage SaaS teams with pipeline review and GTM reporting."
                ),
                "industry": "B2B SaaS consulting",
                "website": "https://pipelineharbor.example",
                "notes": "Asked for examples of decision briefs used in forecast calls.",
                "created_at": "2026-04-26T12:55:00+00:00",
            },
            {
                "id": "lead_demo_004",
                "project_id": PROJECT_ID,
                "company_name": "Summit Revenue Partners",
                "contact_name": "Elena Morris",
                "contact_email": "elena@summitrev.example",
                "status": "contacted",
                "company_description": (
                    "Summit Revenue Partners helps B2B SaaS teams improve forecasting, pipeline visibility, and win rates."
                ),
                "industry": "Revenue operations consulting",
                "website": "https://summitrev.example",
                "notes": "Likely cares about lost-deal analysis and faster GTM learning loops.",
                "created_at": "2026-04-26T12:45:00+00:00",
            },
            {
                "id": "lead_demo_005",
                "project_id": PROJECT_ID,
                "company_name": "SignalLoop Revenue",
                "contact_name": "Ethan Carter",
                "contact_email": "ethan@signalloop.example",
                "status": "replied",
                "company_description": (
                    "SignalLoop Revenue helps SaaS teams improve pipeline visibility and sales execution."
                ),
                "industry": "Revenue operations consulting",
                "website": "https://signalloop.example",
                "notes": (
                    "Candidate fit reason: They already advise on pipeline performance, so win-loss "
                    "analysis is a strong conversation starter and a plausible pilot buyer."
                ),
                "created_at": "2026-04-26T12:30:00+00:00",
            },
        ],
        "outreach_logs.json": [
            {
                "id": "outreach_demo_001",
                "project_id": PROJECT_ID,
                "lead_id": "lead_demo_001",
                "asset_pack_id": "asset_pack_demo_win_loss",
                "channel": "email",
                "message": (
                    "Subject: Quick way to find why deals are slipping\n\n"
                    "Hi Maya,\n\n"
                    "I help SaaS revenue teams turn call notes, CRM context, and post-deal feedback "
                    "into a weekly win-loss brief that shows why deals are lost, delayed, or discounted.\n\n"
                    "If you want, I can send the pilot outline and sample brief."
                ),
                "status": "draft",
                "reply_text": None,
                "created_at": "2026-04-26T13:35:00+00:00",
            },
            {
                "id": "outreach_demo_002",
                "project_id": PROJECT_ID,
                "lead_id": "lead_demo_002",
                "asset_pack_id": "asset_pack_demo_win_loss",
                "channel": "email",
                "message": (
                    "Subject: One way to tighten lost-deal feedback\n\n"
                    "Hi Jon,\n\n"
                    "We package recent lost and stalled deals into a weekly decision brief for revenue "
                    "leaders so the team can see which objections and process gaps keep repeating.\n\n"
                    "Happy to share the sample output if useful."
                ),
                "status": "draft",
                "reply_text": None,
                "created_at": "2026-04-26T13:30:00+00:00",
            },
            {
                "id": "outreach_demo_003",
                "project_id": PROJECT_ID,
                "lead_id": "lead_demo_003",
                "asset_pack_id": "asset_pack_demo_win_loss",
                "channel": "email",
                "message": (
                    "Subject: Quick way to find why deals are slipping\n\n"
                    "Hi Jordan,\n\n"
                    "I put together a win-loss analysis pilot for SaaS revenue teams that need clearer "
                    "signal on why deals are lost or delayed without standing up a full analytics stack.\n\n"
                    "Would a short working session next week be useful?"
                ),
                "status": "sent",
                "reply_text": None,
                "created_at": "2026-04-26T13:05:00+00:00",
            },
            {
                "id": "outreach_demo_004",
                "project_id": PROJECT_ID,
                "lead_id": "lead_demo_004",
                "asset_pack_id": "asset_pack_demo_win_loss",
                "channel": "email",
                "message": (
                    "Subject: Turning lost deals into weekly revenue insight\n\n"
                    "Hi Elena,\n\n"
                    "I help revenue teams convert scattered call notes and CRM feedback into a weekly "
                    "brief that shows the real reasons deals stall, slip, or churn.\n\n"
                    "If that is relevant for Summit Revenue Partners, I can share the pilot structure."
                ),
                "status": "sent",
                "reply_text": None,
                "created_at": "2026-04-26T12:50:00+00:00",
            },
            {
                "id": "outreach_demo_005",
                "project_id": PROJECT_ID,
                "lead_id": "lead_demo_005",
                "asset_pack_id": "asset_pack_demo_win_loss",
                "channel": "email",
                "message": (
                    "Subject: Sample win-loss brief for SignalLoop Revenue\n\n"
                    "Hi Ethan,\n\n"
                    "I recorded a short overview of the pilot structure and the weekly decision brief "
                    "format. Let me know if you'd like me to tailor it to a recent deal segment."
                ),
                "status": "replied",
                "reply_text": (
                    "This is relevant. Send the sample brief and a rough pilot price so I can review "
                    "it with our RevOps team."
                ),
                "created_at": "2026-04-26T12:35:00+00:00",
            },
        ],
    }


def write_json(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def create_backup() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUPS_DIR / f"demo_reset_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for filename in FILES_TO_RESET:
        source = DATA_DIR / filename
        if source.exists():
            shutil.copy2(source, backup_dir / filename)

    return backup_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset backend/data JSON files to a small deterministic demo dataset.",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Explicitly allow overwriting local backend/data JSON files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_reset:
        print("Refusing to overwrite local demo data without --confirm-reset.")
        print("No files were modified.")
        print(
            "Run: python backend/scripts/reset_demo_data.py --confirm-reset",
        )
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = create_backup()
    dataset = build_dataset()

    for filename, records in dataset.items():
        write_json(DATA_DIR / filename, records)

    print(f"Demo data reset complete for project {PROJECT_ID}.")
    print(f"Backup folder: {backup_dir}")
    for filename in FILES_TO_RESET:
        target = DATA_DIR / filename
        print(f"Wrote {filename} -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
