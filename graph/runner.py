"""
AegisOps Pipeline Runner

Entry point used by Streamlit UI.

Responsible for:
- creating initial state
- invoking LangGraph workflow
- returning final state
"""


from graph.build_graph import build_graph
from graph.state import AegisOpsState



# Compile graph once
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


    initial_state = {

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

        return {

            **initial_state,

            "error_message": str(e)

        }
