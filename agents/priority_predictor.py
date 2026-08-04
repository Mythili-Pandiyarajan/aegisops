"""
Priority Predictor Agent
Uses the trained XGBoost ITSM model to predict incident priority.

Input:
    state["ticket_fields"]     — base fields from the intake form
    state["predicted_category"] — set by category_classifier, which now
                                   runs before this node (see build_graph.py)
Output:
    predicted_priority
    priority_confidence

Note:
The underlying model was trained on resolution-time ITSM fields
(handle time, reassignment count, closure code) that don't exist for a
brand-new incident — those still fall back to neutral defaults inside
tools/priority_model.py. This node derives what CAN legitimately be
known at creation time (operational category, real open date/time)
instead of relying purely on static form defaults, so at least some of
the model's input reflects the actual incident.
"""
from datetime import datetime

from graph.state import AegisOpsState
from tools.priority_model import predict_priority


# Maps the AegisOps operational category (from the LLM classifier) to
# the closest CI_Cat label the XGBoost model was trained on.
CATEGORY_TO_CI_CAT = {
    "network": "networkcomponents",
    "hardware": "hardware",
    "database": "database",
    "security": "software",
    "email": "software",
    "application": "application",
    "docker": "subapplication",
}


def run_priority_predictor(
    state: AegisOpsState
) -> dict:
    print("\n==============================")
    print("PRIORITY PREDICTOR STARTED")
    print("==============================")

    ticket_fields = dict(
        state.get(
            "ticket_fields",
            {}
        )
    )

    ##########################################################
    # Derive ci_cat from the classified category, if available
    ##########################################################
    predicted_category = state.get(
        "predicted_category"
    )

    if predicted_category:
        ticket_fields["ci_cat"] = CATEGORY_TO_CI_CAT.get(
            predicted_category,
            ticket_fields.get(
                "ci_cat",
                "software"
            ),
        )

    ##########################################################
    # Populate real open date/time features
    ##########################################################
    now = datetime.now()

    ticket_fields.setdefault(
        "open_dow",
        now.weekday()
    )

    ticket_fields.setdefault(
        "open_month",
        now.month
    )

    ticket_fields.setdefault(
        "open_year",
        now.year
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
