"""
AegisOps Pipeline Runner
"""

from graph.build_graph import build_graph
from graph.state import AegisOpsState


print("AegisOps runner updated - uploaded_log_path support enabled")


pipeline = build_graph()


def run_pipeline(
    incident_text: str,
    incident_id: str,
    ticket_fields: dict,
    human_approved: bool = False,
    uploaded_log_path: str | None = None,
):

    print("RUNNER RECEIVED uploaded_log_path:")
    print(uploaded_log_path)


    initial_state: AegisOpsState = {

        "incident_id": incident_id,

        "incident_text": incident_text,

        "ticket_fields": ticket_fields,

        "uploaded_log_path": uploaded_log_path,

        "human_approved": human_approved,

        "needs_human_review": False,

        "approval_required": False,

        "proposed_commands": [],

    }


    try:

        final_state = pipeline.invoke(
            initial_state
        )

        return final_state


    except Exception as e:

        print("PIPELINE ERROR:", e)

        return {
            **initial_state,
            "error_message": str(e)
        }
