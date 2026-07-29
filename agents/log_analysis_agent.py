"""
Log Analysis Agent — searches server.log / nginx.log / docker.log for
lines relevant to the incident (by category keywords + severity markers),
then asks the LLM to synthesize a suspected root cause from those lines.

This is the most differentiating agent in the pipeline -- most fresher
agent projects never touch real log parsing. Uses realistic, messy sample
logs (data/sample_logs/) rather than clean toy examples.
"""

import os
from groq import Groq

from graph.state import AegisOpsState
from tools.log_parser import search_logs

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set.")
        _client = Groq(api_key=api_key)
    return _client


def _synthesize_root_cause(incident_text: str, log_lines: list) -> str:
    if not log_lines:
        return "No relevant log entries found for this incident."

    formatted = "\n".join(f"[{source}] {line}" for source, line in log_lines)

    prompt = (
        f"Incident: {incident_text}\n\n"
        f"Relevant log lines (most severe/relevant first):\n{formatted}\n\n"
        "Based ONLY on these log lines, state the most likely root cause in "
        "1-2 sentences. Reference specific log evidence (e.g. error counts, "
        "process names, timestamps) rather than speculating beyond what the "
        "logs show."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


def run_log_analysis_agent(state: AegisOpsState) -> dict:
    log_lines = search_logs(
        incident_text=state["incident_text"],
        category=state.get("predicted_category"),
        max_lines=8,
    )

    log_findings = "\n".join(f"[{source}] {line}" for source, line in log_lines)
    suspected_root_cause = _synthesize_root_cause(state["incident_text"], log_lines)

    return {
        "log_findings": log_findings,
        "suspected_root_cause": suspected_root_cause,
    }
