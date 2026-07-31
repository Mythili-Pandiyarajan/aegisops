"""
AegisOps - Log Analysis Agent
"""

from tools.log_parser import search_logs
from tools.llm import llm


def run_log_analysis_agent(state):

    incident = state["incident_text"]
    category = state.get("predicted_category")
    uploaded_log = state.get("uploaded_log_path")

    ##########################################################
    # Search Logs
    ##########################################################

    log_hits = search_logs(
        incident_text=incident,
        category=category,
        uploaded_log_path=uploaded_log,
        max_lines=10,
    )

    ##########################################################
    # No Evidence
    ##########################################################

    if not log_hits:

        return {

            "log_findings": "No relevant log evidence found.",

            "suspected_root_cause":
                "Insufficient log evidence to determine the root cause.",

            "llm_response": "",

        }

    ##########################################################
    # Build Evidence
    ##########################################################

    evidence = "\n".join(
        f"[{src}] {line}"
        for src, line in log_hits
    )

    ##########################################################
    # Prompt
    ##########################################################

    prompt = f"""
You are a Senior Site Reliability Engineer.

Use ONLY the supplied evidence.

Incident
--------
{incident}

Category
--------
{category}

Evidence
--------
{evidence}

Return EXACTLY in this format.

ROOT_CAUSE:
(one short sentence)

ANALYSIS:
(2-3 sentences)

NEXT_STEP:
(one recommendation)
"""

    ##########################################################
    # Invoke LLM
    ##########################################################

    response = llm.invoke(prompt)

    if not isinstance(response, str):
        response = str(response)

    ##########################################################
    # Extract Root Cause
    ##########################################################

    root_cause = response

    if "ROOT_CAUSE:" in response:

        try:

            root_cause = (
                response.split("ROOT_CAUSE:")[1]
                .split("ANALYSIS:")[0]
                .strip()
            )

        except Exception:

            root_cause = response.strip()

    ##########################################################

    return {

        "suspected_root_cause": root_cause,

        "llm_response": response,

        "log_findings": evidence,

    }
