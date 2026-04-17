# Intelligent Agent: deep content analysis using GPT
# Extracts features, intent, tone, and structural indicators from the email

from openai import OpenAI
import json
import config


client = OpenAI(api_key=config.OPENAI_API_KEY)


ANALYSIS_PROMPT = """You are an expert email security analyst. Analyse the email below and extract key information.

Return a JSON object with exactly these fields:
{{
  "intent": "brief one-sentence description of what the sender wants",
  "tone": "formal | informal | aggressive | friendly | deceptive | urgent",
  "urgency_level": "low | medium | high",
  "key_entities": ["list", "of", "named", "entities", "sender mentions"],
  "suspicious_indicators": ["list any red flags or suspicious patterns, empty list if none"],
  "has_links": true or false,
  "has_attachments_mentioned": true or false,
  "requests_sensitive_info": true or false,
  "summary": "2-3 sentence plain English summary of the email"
}}

Return ONLY the JSON object, no markdown, no explanation.

Email Details:
From: {from_name} <{from_email}>
Subject: {subject}
Body:
{body}
"""


def analyse(email: dict) -> dict:
    """
    Run deep content analysis on a single email dict.
    Returns a structured dict of extracted features.
    """

    prompt = ANALYSIS_PROMPT.format(
        from_name=email.get("from_name", "Unknown"),
        from_email=email.get("from_email", ""),
        subject=email.get("subject", ""),
        body=email.get("body", "")[:3000],  # cap at 3000 chars to save tokens
    )

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if the model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Return a safe fallback so the pipeline never crashes
        return {
            "intent": "Unable to parse",
            "tone": "unknown",
            "urgency_level": "medium",
            "key_entities": [],
            "suspicious_indicators": [],
            "has_links": False,
            "has_attachments_mentioned": False,
            "requests_sensitive_info": False,
            "summary": raw[:300],
        }
