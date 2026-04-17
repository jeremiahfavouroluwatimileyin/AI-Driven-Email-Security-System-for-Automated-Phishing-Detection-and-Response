# Response Agent: executes the action determined by the Decision Agent
# Generates auto-replies, delegation reports, or phishing alerts

from openai import OpenAI
import json
import config


client = OpenAI(api_key=config.OPENAI_API_KEY)


AUTO_REPLY_PROMPT = """You are a professional email assistant working for {user_name} at {company}.

Write a polite, professional email response to the email below.
The response should be context-aware and address the key points of the original email.
Keep it concise but helpful. Sign off as {user_name}.

Return a JSON object with exactly two fields:
{{
  "subject": "Re: <original subject or a suitable reply subject>",
  "body": "the full email body text"
}}

Return ONLY the JSON object.

Original Email:
From: {from_name} <{from_email}>
Subject: {subject}
Body:
{body}

Key points identified:
{key_points}
"""


DELEGATION_REPORT_PROMPT = """You are preparing an internal escalation report for {company}.

An email has been received that requires human attention. Prepare a concise internal delegation report.

Return a JSON object with exactly these fields:
{{
  "delegate_to_department": "{delegation_target}",
  "delegate_to_email": "{delegation_email}",
  "subject": "ESCALATION: <brief subject>",
  "summary": "3-4 sentence summary of the email and why it is being escalated",
  "key_information": ["bullet point 1", "bullet point 2", "bullet point 3"],
  "recommended_action": "what the receiving department should do",
  "urgency": "low | normal | high | urgent",
  "original_sender": "{from_name} <{from_email}>"
}}

Return ONLY the JSON object.

Original Email:
From: {from_name} <{from_email}>
Subject: {subject}
Body:
{body}

Risk Assessment:
{decision}
"""


PHISHING_REPORT_PROMPT = """You are a cybersecurity analyst at {company}.

A phishing email has been detected. List all the red flags clearly for the user.

Return a JSON object with exactly these fields:
{{
  "threat_level": "medium | high | critical",
  "red_flags": ["specific red flag 1", "specific red flag 2", ...],
  "attack_type": "credential harvesting | advance fee fraud | malware delivery | account takeover | other",
  "recommendation": "brief advice for the user on what to do"
}}

Return ONLY the JSON object.

Phishing Email:
From: {from_name} <{from_email}>
Subject: {subject}
Body:
{body}

Suspicious indicators already detected:
{suspicious_indicators}
"""


def generate_auto_reply(email: dict, decision: dict) -> dict:
    """Generate a context-aware auto-reply for routine emails."""

    prompt = AUTO_REPLY_PROMPT.format(
        user_name=config.USER_NAME,
        company=config.COMPANY_NAME,
        from_name=email.get("from_name", ""),
        from_email=email.get("from_email", ""),
        subject=email.get("subject", ""),
        body=email.get("body", "")[:2000],
        key_points=json.dumps(decision.get("key_points", {}), indent=2),
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "subject": f"Re: {email.get('subject', '')}",
            "body": "Thank you for your email. I will get back to you shortly.\n\nBest regards,\n" + config.USER_NAME,
        }


def generate_delegation_report(email: dict, decision: dict) -> dict:
    """Generate a structured internal delegation report for critical emails."""

    delegation_target = decision.get("delegation_target") or "Management"
    delegation_email = config.DELEGATION_TARGETS.get(delegation_target, "management@techsolutions.com")

    prompt = DELEGATION_REPORT_PROMPT.format(
        company=config.COMPANY_NAME,
        delegation_target=delegation_target,
        delegation_email=delegation_email,
        from_name=email.get("from_name", ""),
        from_email=email.get("from_email", ""),
        subject=email.get("subject", ""),
        body=email.get("body", "")[:2000],
        decision=json.dumps(decision, indent=2),
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw)
        result["delegate_to_email"] = delegation_email
        return result
    except json.JSONDecodeError:
        return {
            "delegate_to_department": delegation_target,
            "delegate_to_email": delegation_email,
            "subject": f"ESCALATION: {email.get('subject', '')}",
            "summary": "This email has been flagged as critical and requires manual review.",
            "key_information": ["Review original email", "Assess urgency", "Respond to sender"],
            "recommended_action": "Review and respond appropriately.",
            "urgency": decision.get("priority", "high"),
            "original_sender": f"{email.get('from_name', '')} <{email.get('from_email', '')}>",
        }


def generate_phishing_report(email: dict, analysis: dict) -> dict:
    """Generate a detailed phishing threat report."""

    prompt = PHISHING_REPORT_PROMPT.format(
        company=config.COMPANY_NAME,
        from_name=email.get("from_name", ""),
        from_email=email.get("from_email", ""),
        subject=email.get("subject", ""),
        body=email.get("body", "")[:2000],
        suspicious_indicators=json.dumps(analysis.get("suspicious_indicators", []), indent=2),
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "threat_level": "high",
            "red_flags": analysis.get("suspicious_indicators", ["Suspicious content detected"]),
            "attack_type": "other",
            "recommendation": "Do not click any links or reply to this email. Block the sender.",
        }
