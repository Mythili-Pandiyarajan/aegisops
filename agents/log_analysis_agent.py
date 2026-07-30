"""
AegisOps - Log Analysis Agent

Responsibilities
----------------
1. Search uploaded log (preferred)
2. Fall back to demo logs (optional)
3. Summarize only actual evidence
4. Never hallucinate a root cause
"""

from langchain_core.messages import HumanMessage

from tools.log_parser import search_logs
from tools.llm import llm


def run_log_analysis_agent(state):
    """
    State expects:

    incident_text
    predicted_category
    uploaded_log_path (optional)

    Returns:
        log_findings
        suspected_root_cause
    """

    incident = state["incident_text"]

    category = state.get("predicted_category")

    uploaded_log = state.get("uploaded_log_path")

    ######################################################
    # Search logs
    ######################################################

    log_hits = search_logs(
        incident_text=incident,
        category=category,
        uploaded_log_path=uploaded_log,
        max_lines=10,
    )

    ######################################################
    # No evidence
    ######################################################

    if len(log_hits) == 0:

        return {

            "log_findings":
                "No relevant log evidence found.",

            "suspected_root_cause":
                (
                    "Insufficient log evidence to determine the root cause. "
                    "Upload authentication, VPN, application, "
                    "system or database logs."
                )
        }

    ######################################################
    # Build context
    ######################################################

    evidence = "\n".join(
        f"[{src}] {line}"
        for src, line in log_hits
    )

    ######################################################
    # Prompt
    ######################################################

    prompt = f"""
You are a Senior Site Reliability Engineer.

You MUST use ONLY the log evidence below.

Never invent errors.

Never mention files that are not shown.

If evidence is insufficient, reply EXACTLY:

Insufficient log evidence to determine root cause.

Incident

{incident}

Category

{category}

Relevant Log Evidence

{evidence}

Return ONLY:

1. Root Cause

2. Supporting Evidence

3. Recommended Next Diagnostic Step
"""

    ######################################################
    # LLM
    ######################################################

    response = llm.invoke(

        [HumanMessage(content=prompt)]

    )

    ######################################################

    return {

        "log_findings": evidence,

        "suspected_root_cause": response.content,

    }
