"""
AegisOps Category Classifier Agent
Classifies incidents into operational categories.
Uses Groq LLM for semantic classification.
Falls back safely if classification fails.
"""
import os
import json
from groq import Groq
from graph.state import AegisOpsState
CATEGORIES = [
    "network",
    "hardware",
    "database",
    "security",
    "email",
    "application",
    "docker",
]
_client = None
def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get(
            "GROQ_API_KEY"
        )
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY missing"
            )
        _client = Groq(
            api_key=api_key
        )
    return _client
SYSTEM_PROMPT = f"""
You are an IT operations incident classifier.
Classify the incident into exactly ONE category.
Allowed categories:
{", ".join(CATEGORIES)}
Rules:
docker/container failures -> docker
OOMKilled/memory limit/container crash -> docker
disk, CPU, RAM, filesystem -> hardware
API/service/nginx/application errors -> application
SQL/database failures -> database
login/authentication/credential/brute-force/unauthorized access issues -> security
VPN unauthorized access, brute force, or credential attacks against VPN -> security
VPN session limit, capacity, or connectivity issues (no breach indicated) -> network
SMTP/mail failures -> email
Network connectivity/DNS/firewall -> network
Return ONLY JSON:
{{
"category":"category_name",
"confidence":0.0
}}
"""
def run_category_classifier(
    state: AegisOpsState
) -> dict:
    print("\n==============================")
    print("CATEGORY CLASSIFIER STARTED")
    print("==============================")
    incident_text = state.get(
        "incident_text",
        ""
    )
    print(
        "INCIDENT:",
        incident_text
    )
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":"system",
                    "content":SYSTEM_PROMPT
                },
                {
                    "role":"user",
                    "content":incident_text
                }
            ],
            temperature=0.1,
            max_tokens=100,
        )
        raw = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )
        print(
            "RAW RESPONSE:",
            raw
        )
        # Remove markdown wrapper if present
        cleaned = (
            raw
            .replace("```json","")
            .replace("```","")
            .strip()
        )
        parsed = json.loads(
            cleaned
        )
        category = parsed.get(
            "category",
            "UNKNOWN"
        ).lower()
        confidence = float(
            parsed.get(
                "confidence",
                0.0
            )
        )
        if category not in CATEGORIES:
            category = "UNKNOWN"
        return {
            "predicted_category":
                category,
            "category_confidence":
                confidence,
        }
    except Exception as e:
        print(
            "CATEGORY CLASSIFIER ERROR:",
            e
        )
        return {
            "predicted_category":
                "UNKNOWN",
            "category_confidence":
                0.0,
            "error_message":
                str(e),
        }
