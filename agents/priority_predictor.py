"""
Priority Predictor Agent
Uses the trained XGBoost ITSM model to predict incident priority.
Input:
    state["ticket_fields"]
    state["predicted_category"]  (from category_classifier, must run first)
Output:
    predicted_priority
    priority_confidence
"""
from datetime import datetime
from graph.state import AegisOpsState
from tools.priority_model import predict_priority

# Maps the AegisOps operational category (from the LLM classifier)
# to the closest CI_Cat label the XGBoost model was trained on.
CATEGORY_TO_CI_CAT = {
    "network": "networkcomponents",
    "hardware": "hardware",
    "database": "database",
    "security": "software",
    "email": "software",
    "application": "application",
    "docker": "subapplication",
}


def run_priority_predictor(state: AegisOpsState) -> dict:
    print("\n==============================")
    print("PRIORITY PREDICTOR STARTED")
    print("==============================")

    ticket_fields = dict(state.get("ticket_fields", {}))

    predicted_category = state.get("predicted_category")
    if predicted_category:
        ticket_fields["ci_cat"] = CATEGORY_TO_CI_CAT.get(
            predicted_category, ticket_fields.get("ci_cat", "software")
        )

    now = datetime.now()
    ticket_fields.setdefault("open_dow", now.weekday())
    ticket_fields.setdefault("open_month", now.month)
    ticket_fields.setdefault("open_year", now.year)

    print("INPUT FIELDS:")
    print(ticket_fields)

    try:
        priority, confidence = predict_priority(ticket_fields)
        print("PREDICTED PRIORITY:", priority)
        print("CONFIDENCE:", confidence)
        return {
            "predicted_priority": priority,
            "priority_confidence": float(confidence),
        }
    except Exception as e:
        print("PRIORITY MODEL ERROR:", e)
        return {
            "predicted_priority": "Unknown",
            "priority_confidence": 0.0,
            "error_message": str(e),
        }
