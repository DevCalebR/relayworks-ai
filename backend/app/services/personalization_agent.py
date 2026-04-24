import re

from app.services.research_agent import generate_openai_text

PLACEHOLDER_PATTERNS = [
    r"\[[^\]]*name[^\]]*\]",
    r"\[name\]",
    r"\[your name\]",
    r"\[company\]",
    r"\[specific field\]",
    r"<insert[^>]*>",
    r"\{\{[^{}]+\}\}",
]


def _normalized_whitespace(text: str) -> str:
    return " ".join(text.split())


def _contains_placeholder(message: str) -> bool:
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in PLACEHOLDER_PATTERNS)


def _context_signals(lead: dict) -> list[str]:
    signals = []
    company_name = str(lead.get("company_name") or "").strip()
    industry = str(lead.get("industry") or "").strip()
    company_description = str(lead.get("company_description") or "").strip()
    notes = str(lead.get("notes") or "").strip()
    for value in (company_name, industry, company_description, notes):
        if value:
            signals.append(value)
    return signals


def _first_name_from_contact_name(contact_name: str) -> str:
    tokens = [token.strip(" ,.") for token in contact_name.split() if token.strip(" ,.")]
    if not tokens:
        return ""
    prefixes = {"mr", "mrs", "ms", "miss", "dr", "prof"}
    while tokens and tokens[0].lower().rstrip(".") in prefixes:
        tokens.pop(0)
    return tokens[0] if tokens else ""


def _greeting_name(lead: dict) -> str:
    contact_name = str(lead.get("contact_name") or "").strip()
    first_name = _first_name_from_contact_name(contact_name)
    return first_name or contact_name or "there"


def _has_required_context(message: str, lead: dict) -> bool:
    company_name = str(lead.get("company_name") or "").strip()
    industry = str(lead.get("industry") or "").strip()
    lowered = message.lower()
    if company_name and company_name.lower() in lowered:
        return True
    if industry and industry.lower() in lowered:
        return True
    return not (company_name or industry)


def _is_short_enough(message: str) -> bool:
    return len(message.split()) <= 140


def _is_valid_message(message: str, lead: dict) -> bool:
    cleaned = message.strip()
    return bool(
        cleaned
        and not _contains_placeholder(cleaned)
        and _has_required_context(cleaned, lead)
        and _is_short_enough(cleaned)
        and "\n\nHi,\n" not in cleaned
        and "\n\nHi ,\n" not in cleaned
        and not cleaned.startswith("Hi,\n")
        and not cleaned.startswith("Hi ,\n")
    )


def _lead_context_text(lead: dict) -> str:
    parts = []
    company_name = str(lead.get("company_name") or "").strip()
    industry = str(lead.get("industry") or "").strip()
    company_description = str(lead.get("company_description") or "").strip()
    website = str(lead.get("website") or "").strip()
    notes = str(lead.get("notes") or "").strip()
    if company_name:
        parts.append(f"Company: {company_name}")
    if industry:
        parts.append(f"Industry: {industry}")
    if company_description:
        parts.append(f"Company description: {company_description}")
    if website:
        parts.append(f"Website: {website}")
    if notes:
        parts.append(f"Notes: {notes}")
    return "\n".join(parts)


def _notes_focus_phrase(notes: str) -> str:
    cleaned = notes.strip().rstrip(".")
    lowered = cleaned.lower()
    for prefix in (
        "likely cares about ",
        "likely interested in ",
        "cares about ",
        "interested in ",
        "focused on ",
        "priority is ",
    ):
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    return cleaned.strip()


def _extract_subject(message: str) -> str:
    for line in message.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            return stripped.split(":", 1)[1].strip()
        if stripped:
            break
    return ""


def _fallback_outreach_message(lead: dict, asset_pack: dict, channel: str) -> str:
    company_name = str(lead.get("company_name") or "your team").strip()
    industry = str(lead.get("industry") or "").strip()
    company_description = str(lead.get("company_description") or "").strip()
    notes = _notes_focus_phrase(str(lead.get("notes") or ""))
    subject = str(asset_pack.get("cold_outreach_email_subject") or "Quick idea for your pipeline").strip()

    body_lines = [
        f"Hi {_greeting_name(lead)},",
        "",
        f"I took a look at {company_name} and the work you do{f' in {industry.lower()}' if industry else ''}.",
        "A practical angle here is turning recent lost or stalled deals into a tighter feedback loop for pipeline reviews and win-rate decisions.",
    ]
    if notes:
        body_lines.append(f"Given your likely focus on {notes}, a small pilot could surface the exact objections and loss patterns your team can act on this quarter.")
    elif company_description:
        body_lines.append(f"That seems especially relevant for teams like {company_name} that are focused on {company_description.rstrip('.')}.")
    body_lines.append("If useful, I can send a lean pilot outline and sample output this week.")

    body = "\n".join(body_lines)
    message = f"Subject: {subject}\n\n{body}" if channel == "email" else _normalized_whitespace(body)
    return _post_process_message(message, lead)


def _fallback_follow_up_message(
    lead: dict,
    latest_outreach: dict,
    channel: str,
    asset_pack: dict | None = None,
) -> str:
    company_name = str(lead.get("company_name") or "your team").strip()
    contact_name = _greeting_name(lead)
    industry = str(lead.get("industry") or "").strip()
    notes = _notes_focus_phrase(str(lead.get("notes") or ""))
    reply_text = str(latest_outreach.get("reply_text") or "").strip()
    original_subject = _extract_subject(str(latest_outreach.get("message") or ""))
    pilot_offer = str((asset_pack or {}).get("pilot_offer") or "").strip()

    if reply_text:
        subject = f"Re: {original_subject}" if original_subject else f"{company_name} pilot outline"
        body_lines = [
            f"Hi {contact_name},",
            "",
            "Thanks for the quick reply.",
            f"You mentioned that timing is tight, so I'll keep this lightweight for {company_name}.",
            f"I can send a lean pilot outline and sample output tailored to how {company_name} reviews lost and stalled deals{f' in {industry.lower()}' if industry else ''}.",
        ]
        if notes:
            body_lines.append(f"I'll keep it focused on {notes} so it's easy to evaluate quickly.")
        elif pilot_offer:
            body_lines.append(pilot_offer)
        body_lines.append("Would it help if I sent that over today?")
    else:
        subject = f"Re: {original_subject}" if original_subject else f"Idea for {company_name}"
        body_lines = [
            f"Hi {contact_name},",
            "",
            f"Following up with a different angle for {company_name}: a small review of recent lost deals can show where forecast risk and win-rate drag are actually coming from.",
            "That usually gives teams one concrete message, process, or qualification change they can use in the next pipeline review.",
        ]
        if notes:
            body_lines.append(f"Is faster learning on {notes} a priority right now?")
        else:
            body_lines.append("Would a sample output help you assess whether this is worth a pilot?")

    body = "\n".join(body_lines)
    message = f"Subject: {subject}\n\n{body}" if channel == "email" else _normalized_whitespace(body)
    return _post_process_message(message, lead)


def _clean_message(message: str) -> str:
    cleaned = message.replace("[Name]", "").replace("[Your Name]", "").replace("[Company]", "")
    cleaned = cleaned.replace("[First Name]", "").replace("[Contact Name]", "")
    cleaned = cleaned.replace("[specific field]", "revenue operations")
    cleaned = re.sub(r"<insert[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\{\{[^{}]+\}\}", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _post_process_message(message: str, lead: dict) -> str:
    cleaned = _clean_message(message)
    greeting_name = _greeting_name(lead)
    if greeting_name != "there":
        greeting_patterns = [
            (r"\n\n(?:Hi|Hello|Hey)\s*(?:there)?\s*,\n\n", f"\n\nHi {greeting_name},\n\n"),
            (r"\n\n(?:Hi|Hello|Hey)\s*(?:there)?\s*,\n", f"\n\nHi {greeting_name},\n"),
            (r"^(?:Hi|Hello|Hey)\s*(?:there)?\s*,\n\n", f"Hi {greeting_name},\n\n"),
            (r"^(?:Hi|Hello|Hey)\s*(?:there)?\s*,\n", f"Hi {greeting_name},\n"),
            (r"^((?:Subject:[^\n]*\n\n))(?:Hi|Hello|Hey)\s+[^,\n]+,\n", rf"\1Hi {greeting_name},\n"),
            (r"^(?:Hi|Hello|Hey)\s+[^,\n]+,\n", f"Hi {greeting_name},\n"),
        ]
        for pattern, replacement in greeting_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, count=1, flags=re.IGNORECASE)
    cleaned = re.sub(r"^Subject:\s*Re:\s*Re:\s*", "Subject: Re: ", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _generate_with_retry(prompt: str, stricter_prompt: str) -> str | None:
    outputs = []
    first = generate_openai_text(prompt)
    if first:
        outputs.append(first.strip())
    second = generate_openai_text(stricter_prompt)
    if second:
        outputs.append(second.strip())
    for output in outputs:
        if output:
            return output
    return None


def generate_personalized_outreach(
    lead: dict,
    asset_pack: dict,
    channel: str,
) -> tuple[str, str]:
    lead_context = _lead_context_text(lead)
    base_message = str(asset_pack.get("cold_outreach_email_body") or "").strip()
    base_subject = str(asset_pack.get("cold_outreach_email_subject") or "").strip()
    prompt = (
        "Write a concise personalized B2B outreach message.\n"
        "Plain text only. No markdown. No placeholders.\n"
        "Use the company context naturally. Mention the company name. Mention the industry when useful.\n"
        "Reference the business context from the description or notes if available.\n"
        "Keep it short, value-driven, and realistic for cold outbound.\n"
        "If contact_name is available, greet the recipient with their first name.\n"
        "If channel=email, start with 'Subject:' then a blank line then the body.\n\n"
        f"Channel: {channel}\n"
        f"Lead context:\n{lead_context}\n\n"
        f"Asset pack subject: {base_subject}\n"
        f"Asset pack message: {base_message}"
    )
    stricter_prompt = (
        prompt
        + "\n\nRequirements: no unresolved placeholders, under 140 words, include the company name, and do not use generic filler."
    )
    for candidate in (
        generate_openai_text(prompt),
        generate_openai_text(stricter_prompt),
    ):
        if candidate:
            cleaned = _post_process_message(candidate.strip(), lead)
            if _is_valid_message(cleaned, lead):
                return cleaned, "openai"

    fallback = _fallback_outreach_message(lead=lead, asset_pack=asset_pack, channel=channel)
    return fallback, "fallback"


def generate_personalized_follow_up(
    lead: dict,
    latest_outreach: dict,
    channel: str,
    asset_pack: dict | None = None,
) -> tuple[str, str]:
    lead_context = _lead_context_text(lead)
    original_message = str(latest_outreach.get("message") or "").strip()
    reply_text = str(latest_outreach.get("reply_text") or "").strip()
    prompt = (
        "Write a concise personalized B2B follow-up message.\n"
        "Plain text only. No markdown. No placeholders.\n"
        "Reference the prior outreach, use the lead context naturally, and add a new angle instead of repeating the same pitch.\n"
        "You may ask one soft question. Keep the tone helpful and commercially credible.\n"
        "If reply_text is present, acknowledge it directly and write the next response accordingly.\n"
        "If contact_name is available, greet the recipient with their first name.\n"
        "If channel=email, start with 'Subject:' then a blank line then the body.\n\n"
        f"Channel: {channel}\n"
        f"Lead context:\n{lead_context}\n\n"
        f"Latest outreach: {latest_outreach}\n"
        f"Asset pack context: {asset_pack or {}}\n"
        f"Reply text: {reply_text or 'None'}\n"
        f"Original message: {original_message}"
    )
    stricter_prompt = (
        prompt
        + "\n\nRequirements: under 140 words, include the company name or industry, no unresolved placeholders, and materially differ from the original."
    )
    for candidate in (
        generate_openai_text(prompt),
        generate_openai_text(stricter_prompt),
    ):
        if candidate:
            cleaned = _post_process_message(candidate.strip(), lead)
            if _is_valid_message(cleaned, lead) and _normalized_whitespace(cleaned.lower()) != _normalized_whitespace(original_message.lower()):
                return cleaned, "openai"

    fallback = _fallback_follow_up_message(
        lead=lead,
        latest_outreach=latest_outreach,
        channel=channel,
        asset_pack=asset_pack,
    )
    return fallback, "fallback"


def message_has_context_signal(message: str, lead: dict) -> bool:
    lowered = message.lower()
    company_name = str(lead.get("company_name") or "").strip().lower()
    industry = str(lead.get("industry") or "").strip().lower()
    company_description = str(lead.get("company_description") or "").strip().lower()
    notes = str(lead.get("notes") or "").strip().lower()
    if company_name and company_name in lowered:
        return True
    if industry and industry in lowered:
        return True
    for fragment in (company_description, notes):
        if fragment:
            words = [word for word in re.split(r"[^a-z0-9]+", fragment) if len(word) > 4]
            if any(word in lowered for word in words[:5]):
                return True
    return not bool(_context_signals(lead))


def message_has_no_placeholders(message: str) -> bool:
    return not _contains_placeholder(message)
