"""
Incident Classifier Agent — determines the incident category:
network / hardware / database / security / email.

Runs in parallel with the priority predictor (see build_graph.py) since
category and priority are independent signals from the same input text.

Uses Groq's free tier (llama3-8b-8192) -- same provider already wired up
for the ITSM Tab 5 AI Assistant.
"""

import os
import json
from groq import Groq

from graph.state import AegisOpsState

CATEGORIES = ["network", "hardware", "database", "security", "email"]

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Add it to your .env "
                "(same key used for the ITSM Tab 5 AI Assistant)."
            )
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = f"""You are an IT incident classifier. Given an incident
description, classify it into exactly one of these categories:
{', '.join(CATEGORIES)}

Respond with ONLY a JSON object in this exact format, no other text:
{{"category": "<one of {CATEGORIES}>", "confidence": <float 0-1>}}
"""


def run_category_classifier(state: AegisOpsState) -> dict:
    incident_text = state["incident_text"]

    client = _get_client()
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": incident_text},
        ],
        temperature=0.1,
        max_tokens=100,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip("`").replace("json", "", 1).strip()
        parsed = json.loads(cleaned)

    predicted_category = parsed.get("category")
    if predicted_category not in CATEGORIES:
        predicted_category = "UNKNOWN"

    return {
        "predicted_category": predicted_category,
        "category_confidence": float(parsed.get("confidence", 0.0)),
    }
