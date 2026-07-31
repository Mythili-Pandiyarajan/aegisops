"""
AegisOps Pipeline Runner
"""

print("===================================")
print("AegisOps runner updated - uploaded_log_path support enabled")
print("Loaded runner from:", __file__)
print("===================================")

import traceback

from graph.build_graph import build_graph
from graph.state import AegisOpsState


print("NEW RUNNER LOADED:", __file__)
print("AegisOps runner updated - uploaded_log_path support enabled")

pipeline = build_graph()



def run_pipeline(
    incident_text: str,
    incident_id: str,
    ticket_fields: dict,
    human_approved: bool = False,
    uploaded_log_path: str | None = None,
):

    print("PIPELINE RUN STARTED")

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

        result = pipeline.invoke(
            initial_state
        )

        return result


    except Exception as e:

        traceback.print_exc()

        return {

            **initial_state,

            "error_message": str(e)

        }
