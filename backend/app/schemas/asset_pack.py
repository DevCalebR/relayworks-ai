from pydantic import BaseModel


class AssetPackRequest(BaseModel):
    project_id: str
    launch_plan_id: str | None = None
    use_latest_launch_plan: bool = False


class FAQItem(BaseModel):
    question: str
    answer: str


class AssetPackResponse(BaseModel):
    id: str
    project_id: str
    launch_plan_id: str
    source_run_id: str
    headline: str
    one_sentence_pitch: str
    landing_page_hero: str
    landing_page_subheadline: str
    key_benefits: list[str]
    offer_stack: list[str]
    call_to_action: str
    cold_outreach_email_subject: str
    cold_outreach_email_body: str
    linkedin_dm: str
    discovery_call_script: list[str]
    pilot_offer: str
    pricing_blurb: str
    faq: list[FAQItem]
    created_at: str
