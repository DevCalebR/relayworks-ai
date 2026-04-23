OPERATOR_MODES = (
    "research_operator",
    "content_operator",
    "leadgen_operator",
    "product_operator",
)

MODE_PROMPTS = {
    "research_operator": {
        "label": "Research Operator",
        "guidance": (
            "Identify profitable research, analysis, and intelligence offers that can start as a service "
            "and later become a product."
        ),
        "fallback": {
            "niche": "B2B competitive intelligence for service businesses",
            "target_customer": "Boutique agencies and consulting firms",
            "core_problem": "Teams need faster market insight without hiring full-time analysts",
            "offer": "Recurring competitor and market brief service",
            "mvp": "Weekly insight dashboard with manual analyst review",
            "distribution_channel": "Founder-led outbound to agency owners",
            "monetization_model": "Monthly retainer with setup fee",
            "opportunity_score": 8,
            "confidence_score": 7,
            "reasoning": (
                "The problem is expensive, recurring, and easy to validate with service-led delivery before "
                "building software."
            ),
            "next_actions": [
                "Interview five agency owners about research bottlenecks",
                "Package a sample weekly intelligence brief",
                "Pitch a paid pilot to one niche agency segment",
            ],
            "deliverables": [
                "Sample insight report",
                "Pilot scope document",
                "Outreach list of ideal buyers",
            ],
        },
    },
    "content_operator": {
        "label": "Content Operator",
        "guidance": (
            "Identify profitable content, newsletter, media, or content-production opportunities with fast "
            "distribution and monetization."
        ),
        "fallback": {
            "niche": "Niche B2B content engine for regulated service industries",
            "target_customer": "Small firms in finance, legal, and compliance-heavy sectors",
            "core_problem": "Firms need consistent expert content but lack production capacity",
            "offer": "AI-assisted authority content subscription",
            "mvp": "Monthly content package with briefs, drafts, and distribution calendar",
            "distribution_channel": "LinkedIn content plus outbound email",
            "monetization_model": "Monthly subscription",
            "opportunity_score": 7,
            "confidence_score": 6,
            "reasoning": (
                "Content demand is steady, delivery is lightweight, and a service wrapper makes early sales easier "
                "than launching a pure media brand."
            ),
            "next_actions": [
                "Choose one niche with expensive customer acquisition",
                "Create three sample authority posts and one newsletter",
                "Offer a low-friction first-month content pilot",
            ],
            "deliverables": [
                "Editorial calendar",
                "Three post templates",
                "Pilot pricing sheet",
            ],
        },
    },
    "leadgen_operator": {
        "label": "Leadgen Operator",
        "guidance": (
            "Identify profitable lead generation offers, outbound systems, or qualification workflows that create "
            "pipeline quickly."
        ),
        "fallback": {
            "niche": "AI-assisted outbound prospecting for niche B2B providers",
            "target_customer": "Local and vertical service companies with high-ticket deals",
            "core_problem": "Teams need more qualified leads but cannot maintain consistent prospecting",
            "offer": "Managed lead sourcing and qualification service",
            "mvp": "Weekly lead list with personalized outreach suggestions",
            "distribution_channel": "Cold email and partner referrals",
            "monetization_model": "Retainer plus performance bonus",
            "opportunity_score": 8,
            "confidence_score": 7,
            "reasoning": (
                "Lead generation maps directly to revenue, buyers understand the outcome, and manual support can "
                "bridge product gaps early."
            ),
            "next_actions": [
                "Pick one vertical with high customer lifetime value",
                "Assemble a sample lead list and outreach sequence",
                "Offer a two-week paid qualification sprint",
            ],
            "deliverables": [
                "Lead qualification rubric",
                "Sample outreach sequence",
                "Pilot KPI dashboard",
            ],
        },
    },
    "product_operator": {
        "label": "Product Operator",
        "guidance": (
            "Identify profitable software or workflow-tool MVPs that solve a painful business problem and can be "
            "validated quickly."
        ),
        "fallback": {
            "niche": "Vertical AI workflow tool for ops-heavy SMB teams",
            "target_customer": "Operations managers at midsize service companies",
            "core_problem": "Teams waste time coordinating repetitive workflows across fragmented tools",
            "offer": "AI workflow copilot for one high-friction operational task",
            "mvp": "Narrow dashboard that automates task intake, triage, and reporting",
            "distribution_channel": "Founder demos to niche communities and existing operators",
            "monetization_model": "Per-seat subscription with onboarding fee",
            "opportunity_score": 7,
            "confidence_score": 6,
            "reasoning": (
                "Software can scale well, but product risk is higher than service-led modes until one workflow is "
                "validated with paying users."
            ),
            "next_actions": [
                "Choose one workflow with clear operational pain",
                "Prototype a clickable demo for that single workflow",
                "Run discovery and demo calls with five target buyers",
            ],
            "deliverables": [
                "Workflow map",
                "MVP screen list",
                "Demo script",
            ],
        },
    },
}


def get_mode_prompt(mode: str) -> dict:
    return MODE_PROMPTS.get(mode, MODE_PROMPTS["research_operator"])
