"""
Incident Classifier Agent — determines the incident category:
network / hardware / database / security / email.

Runs in parallel with the priority predictor (see build_graph.py) since
category and priority are independent signals from the same input text.
"""

from graph.state import AegisOpsState


def run_category_classifier(state: AegisOpsState) -> dict:
    incident_text = state["incident_text"]

    # TODO: replace with real LLM call or trained classifier
    predicted_category = "network"
    confidence = 0.0

    return {
        "predicted_category": predicted_category,
        "category_confidence": confidence,
    }
