from app.services.research_agent import generate_openai_text


def _extract_subject(message: str) -> str:
    for line in message.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            return stripped.split(":", 1)[1].strip()
        if stripped:
            break
    return ""


def _normalize_compare_text(message: str) -> str:
    return " ".join(message.lower().split())


def _build_fallback_follow_up(
    lead: dict,
    latest_outreach: dict,
    channel: str,
    asset_pack: dict | None = None,
) -> str:
    contact_name = str(lead.get("contact_name") or "there").strip()
    original_subject = _extract_subject(str(latest_outreach.get("message") or ""))
    pilot_offer = str((asset_pack or {}).get("pilot_offer") or "").strip()
    pitch = str((asset_pack or {}).get("one_sentence_pitch") or "").strip()
    reply_text = str(latest_outreach.get("reply_text") or "").strip()

    if reply_text:
        subject = f"Re: {original_subject}" if original_subject else "Re: Quick follow-up"
        body = (
            f"Hi {contact_name},\n\n"
            "Thanks for the reply. To keep this lightweight, I can narrow this into a short pilot "
            "with the exact inputs, sample output, and timeline so your team can decide quickly."
        )
        if pilot_offer:
            body += f" {pilot_offer}"
        body += "\n\nWould it help if I sent that over today?"
    else:
        subject = (
            f"Re: {original_subject}"
            if original_subject
            else "Quick follow-up on the revenue brief idea"
        )
        body = (
            f"Hi {contact_name},\n\n"
            "Following up with a slightly different angle: we can turn a small set of recent lost "
            "or stalled deals into a brief your team can use in the next pipeline review."
        )
        if pitch:
            body += f" {pitch}"
        body += (
            "\n\nIf useful, I can send the sample output and pilot scope so you can assess it this week."
        )

    if channel == "email":
        return f"Subject: {subject}\n\n{body}"
    return body


def generate_follow_up_message(
    lead: dict,
    latest_outreach: dict,
    channel: str,
    asset_pack: dict | None = None,
) -> tuple[str, str]:
    original_message = str(latest_outreach.get("message") or "").strip()
    reply_text = str(latest_outreach.get("reply_text") or "").strip()

    prompt = (
        "You write concise B2B outbound follow-up messages.\n"
        "Write plain text only. Do not use markdown.\n"
        "Keep the message polite, short, value-driven, and commercially specific.\n"
        "Reference the previous note, change the angle slightly, avoid repeating the same phrasing, "
        "and add either urgency or one new concrete value point.\n"
        "If reply_text is present, write a response to that reply instead of a generic follow-up.\n"
        "If the channel is email, start with a 'Subject:' line, then a blank line, then the body.\n"
        "Keep the output under 120 words.\n\n"
        f"Channel: {channel}\n"
        f"Lead: {lead}\n"
        f"Latest outreach: {latest_outreach}\n"
        f"Asset pack context: {asset_pack or {}}\n"
        f"Reply text: {reply_text or 'None'}\n"
        f"Original message: {original_message}"
    )
    openai_output = generate_openai_text(prompt)
    if openai_output:
        cleaned_output = openai_output.strip()
        if (
            cleaned_output
            and _normalize_compare_text(cleaned_output) != _normalize_compare_text(original_message)
        ):
            return cleaned_output, "openai"

    return _build_fallback_follow_up(lead, latest_outreach, channel, asset_pack), "fallback"
