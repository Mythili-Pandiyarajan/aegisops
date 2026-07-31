"""
AegisOps - Log Analysis Agent

Analyzes incident logs and identifies root cause.
"""

from tools.log_parser import search_logs
from tools.llm import llm


def run_log_analysis_agent(state):

    print("\n==============================")
    print("LOG ANALYSIS AGENT STARTED")
    print("==============================")

    incident = state.get(
        "incident_text",
        ""
    )

    category = state.get(
        "predicted_category",
        ""
    )

    uploaded_log = state.get(
        "uploaded_log_path"
    )


    print("CATEGORY:", category)
    print("INCIDENT:")
    print(incident)


    ##########################################################
    # Search Logs
    ##########################################################

    log_hits = search_logs(
        incident_text=incident,
        category=category,
        uploaded_log_path=uploaded_log,
        max_lines=10,
    )


    print("\nLOG HITS FOUND:")
    print(log_hits)


    ##########################################################
    # No Evidence
    ##########################################################

    if not log_hits:

        return {

            "log_findings":
                "No relevant log evidence found.",

            "suspected_root_cause":
                "Unable to determine root cause because no matching logs were found.",

            "llm_response":
                "",

            "log_confidence":
                0.0,

        }


    ##########################################################
    # Build Evidence
    ##########################################################

    evidence = "\n".join(
        f"[{src}] {line}"
        for src, line in log_hits
    )


    print("\nEVIDENCE:")
    print(evidence)



    ##########################################################
    # LLM Analysis
    ##########################################################

    prompt = f"""

You are a Senior Security Operations Engineer.

Analyze ONLY the evidence below.

Incident:
{incident}

Category:
{category}


Log Evidence:
{evidence}


Return:

ROOT_CAUSE:
one sentence

ANALYSIS:
short explanation using evidence

NEXT_STEP:
recommended action

"""


    response = llm.invoke(prompt)


    if not isinstance(response, str):
        response = str(response)


    print("\nLLM RESPONSE:")
    print(response)



    ##########################################################
    # Extract Root Cause
    ##########################################################

    root_cause = response


    if "ROOT_CAUSE:" in response:

        try:

            root_cause = (
                response
                .split("ROOT_CAUSE:")[1]
                .split("ANALYSIS:")[0]
                .strip()
            )

        except Exception:

            root_cause = response.strip()



    ##########################################################
    # Return State
    ##########################################################

    return {


        "log_findings":
            evidence,


        "suspected_root_cause":
            root_cause,


        "llm_response":
            response,


        "log_confidence":
            0.9,


    }
