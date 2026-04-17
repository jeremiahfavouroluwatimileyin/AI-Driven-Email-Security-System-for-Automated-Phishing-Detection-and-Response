# Decision Agent: evaluates features from the Intelligent Agent
# Assigns a risk score and classifies the email into one of four categories:
# routine, critical, spam, phishing

from openai import OpenAI
import json
import config


client = OpenAI(api_key=config.OPENAI_API_KEY)


DECISION_PROMPT = """You are an email security decision engine for a professional company called "{company}".

Given the email details and the analysis below, you must:
1. Compute a risk score from 0 to 100 (0 = completely safe, 100 = certain threat)
2. Classify the email into exactly one category: routine, critical, spam, or phishing
3. Provide a breakdown of how you scored it

Classification rules:
- routine: legitimate, low-to-medium priority emails that can be auto-responded
- critical: legitimate but high-stakes emails requiring human attention (legal, HR, security incidents, contract matters, urgent deadlines from real known senders)
- spam: unsolicited bulk or promotional email with no malicious intent
- phishing: deceptive emails attempting to steal information, money, or credentials

Return a JSON object with exactly these fields:
{{
  "classification": "routine | critical | spam | phishing",
  "risk_score": integer 0-100,
  "risk_level": "low | medium | high",
  "priority": "low | normal | high | urgent",
  "score_breakdown": {{
    "sender_credibility": integer 0-25,
    "content_legitimacy": integer 0-25,
    "link_safety": integer 0-25,
    "behavioural_patterns": integer 0-25
  }},
  "reasoning": "2-3 sentence explanation of the classification decision",
  "delegation_target": "HR | Security | Finance | Legal | IT | Management | null",
  "key_points": {{
    "urgency": "extracted urgency detail or null",
    "deadline": "extracted deadline or null",
    "action_required": "what action is needed or null",
    "sender_role": "sender's title or organisation or null",
    "financial_amount": "any money mentioned or null"
  }}
}}

Return ONLY the JSON object.

Company: {company}
Email From: {from_name} <{from_email}>
Subject: {subject}

Intelligent Agent Analysis:
{analysis}
"""


def evaluate(email: dict, analysis: dict) -> dict:
    """
    Takes the original email and the Intelligent Agent's analysis.
    Returns a classification decision with risk score and metadata.
    """

    prompt = DECISION_PROMPT.format(
        company=config.COMPANY_NAME,
        from_name=email.get("from_name", "Unknown"),
        from_email=email.get("from_email", ""),
        subject=email.get("subject", ""),
        analysis=json.dumps(analysis, indent=2),
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
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
            "classification": "routine",
            "risk_score": 30,
            "risk_level": "low",
            "priority": "normal",
            "score_breakdown": {
                "sender_credibility": 20,
                "content_legitimacy": 20,
                "link_safety": 25,
                "behavioural_patterns": 20,
            },
            "reasoning": "Could not parse decision. Defaulting to routine.",
            "delegation_target": None,
            "key_points": {
                "urgency": None,
                "deadline": None,
                "action_required": None,
                "sender_role": None,
                "financial_amount": None,
            },
        }
