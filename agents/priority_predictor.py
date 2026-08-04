"""
Priority Predictor Agent

Determines incident priority using the ITSM priority matrix
(Priority = min(Impact, Urgency)) -- see tools/priority_rules.py for
why this replaced the XGBoost model for real-time triage.

Input:
    state["ticket_fields"]["impact"]   -- 1 (highest) to 5 (lowest)
    state["ticket_fields"]["urgency"]  -- 1 (highest) to 5 (lowest)

Output:
    predicted_priority
    priority_confidence
"""
from graph.state import AegisOpsState
from tools.priority_rules import predict_priority_from_impact_urgency


# Used only if impact/urgency are missing from ticket_fields entirely
# (e.g. an older incident record, or a caller that hasn't been updated
# to pass them yet). 3 = "moderate", the most common historical value.
DEFAULT_IMPACT = 3
DEFAULT_URGENCY = 3


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

    impact = ticket_fields.get(
        "impact",
        DEFAULT_IMPACT,
    )

    urgency = ticket_fields.get(
        "urgency",
        DEFAULT_URGENCY,
    )

    print("IMPACT:", impact)
    print("URGENCY:", urgency)

    try:
        priority, confidence = predict_priority_from_impact_urgency(
            impact,
            urgency,
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
            "PRIORITY RULE ERROR:",
            e
        )
        return {
            "predicted_priority": "Unknown",
            "priority_confidence": 0.0,
            "error_message": str(e),
        }
