"""
AegisOps Pipeline Runner

Entry point used by Streamlit UI.

Responsible for:
- creating initial LangGraph state
- invoking workflow
- returning final pipeline state
"""

import traceback

from graph.build_graph import build_graph
from graph.state import AegisOpsState


print("RUNNER LOADED:", __file__)


# Compile LangGraph once
pipeline = build_graph()



def run_pipeline(
    incident_text: str,
    incident_id: str,
    ticket_fields: dict,
    human_approved: bool = False,
    uploaded_log_path: str | None = None,
):

    print("\n==============================")
    print("AEGISOPS PIPELINE STARTED")
    print("==============================")

    print("INCIDENT ID:", incident_id)
    print("UPLOADED LOG:", uploaded_log_path)
    print("HUMAN APPROVED:", human_approved)


    initial_state: AegisOpsState = {


        # =====================
        # Input
        # =====================

        "incident_id": incident_id,

        "incident_text": incident_text,

        "ticket_fields": ticket_fields,

        "uploaded_log_path": uploaded_log_path,


        # =====================
        # Approval Flow
        # =====================

        "human_approved": human_approved,


        # =====================
        # Defaults
        # =====================

        "needs_human_review": False,

        "approval_required": False,

        "proposed_commands": [],


        # =====================
        # Metadata
        # =====================

        "current_agent": "starting",

    }



    try:

        final_state = pipeline.invoke(
            initial_state
        )


        print("\n==============================")
        print("PIPELINE COMPLETED")
        print("==============================")


        return final_state



    except Exception as e:


        print("\n==============================")
        print("PIPELINE FAILED")
        print("==============================")


        print(e)

        traceback.print_exc()



        return {

            **initial_state,

            "error_message": str(e),

        }
