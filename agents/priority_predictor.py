"""
Priority Predictor Agent

Uses the trained XGBoost ITSM model to predict incident priority.

Input:
    state["ticket_fields"]

Output:
    predicted_priority
    priority_confidence
"""

from graph.state import AegisOpsState
from tools.priority_model import predict_priority



def run_priority_predictor(
    state: AegisOpsState
) -> dict:


    print("\n==============================")
    print("PRIORITY PREDICTOR STARTED")
    print("==============================")


    ticket_fields = state.get(
        "ticket_fields",
        {}
    )


    print("INPUT FIELDS:")
    print(ticket_fields)



    try:

        priority, confidence = predict_priority(
            ticket_fields
        )


        print(
            "PREDICTED PRIORITY:",
            priority
        )

        print(
            "CONFIDENCE:",
            confidence
        )


        return {

            "predicted_priority": priority,

            "priority_confidence": float(
                confidence
            ),

        }



    except Exception as e:


        print(
            "PRIORITY MODEL ERROR:",
            e
        )


        return {

            "predicted_priority": "Unknown",

            "priority_confidence": 0.0,

            "error_message": str(e),

        }
