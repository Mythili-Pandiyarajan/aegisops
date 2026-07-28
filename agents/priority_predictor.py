"""
Priority Predictor — reuses the trained XGBoost model from the
ITSM-Incident-ML-Prediction project as a tool inside this agent graph.

This is NOT an LLM call. It's a deliberate design choice: a supervised
model trained on real historical ticket data predicts priority more
reliably and far cheaper than asking an LLM to guess from raw text.

NOTE: the underlying model expects structured ticket fields, not raw
free text (see tools/priority_model.py docstring for the full reasoning
and the accuracy tradeoff this implies for brand-new incidents). Pull
those structured fields from state["ticket_fields"] if present -- e.g.
from an incident intake form -- otherwise sensible defaults apply.
"""

from graph.state import AegisOpsState
from tools.priority_model import predict_priority


def run_priority_predictor(state: AegisOpsState) -> dict:
    ticket_fields = state.get("ticket_fields") or {}

    predicted_priority, confidence = predict_priority(ticket_fields)

    return {
        "predicted_priority": predicted_priority,
        "priority_confidence": confidence,
    }
