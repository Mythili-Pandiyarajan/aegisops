"""
AegisOps - Log Analysis Agent
"""

from tools.log_parser import search_logs
from tools.llm import llm


def run_log_analysis_agent(state):

    print("🚀 LOG ANALYSIS STARTED")


    incident = state["incident_text"]

    category = state.get("predicted_category")

    uploaded_log = state.get("uploaded_log_path")


    print("📌 Incident:", incident)
    print("📌 Category:", category)
    print("📌 Uploaded log:", uploaded_log)


    ######################################################
    # Search logs
    ######################################################

    print("🔎 Searching logs...")


    log_hits = search_logs(
        incident_text=incident,
        category=category,
        uploaded_log_path=uploaded_log,
        max_lines=10,
    )


    print("✅ Log search completed")
    print("📄 Logs found:", len(log_hits))


    ######################################################
    # No evidence
    ######################################################

    if len(log_hits) == 0:

        print("⚠️ No log evidence found")

        return {

            "log_findings":
                "No relevant log evidence found.",

            "suspected_root_cause":
                "Insufficient log evidence to determine root cause."
        }


    ######################################################
    # Build context
    ######################################################

    evidence = "\n".join(
        f"[{src}] {line[:300]}"
        for src, line in log_hits
    )


    print("📝 Evidence prepared")


    ######################################################
    # Prompt
    ######################################################

    prompt = f"""
You are a Senior Site Reliability Engineer.

Use ONLY the evidence provided.

Incident:
{incident}

Category:
{category}

Evidence:
{evidence}

Return:

1. Root Cause

2. Supporting Evidence

3. Recommended Next Diagnostic Step
"""


    print("🧠 Sending request to Groq...")


    ######################################################
    # Groq LLM
    ######################################################

    response = llm.invoke(prompt)


    print("✅ Groq response received")


    return {

        "log_findings": evidence,

        "suspected_root_cause": response,

    }
