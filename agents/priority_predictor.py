"""
Priority Predictor — reuses the trained XGBoost model from the
ITSM-Incident-ML-Prediction project as a tool inside this agent graph.

This is NOT an LLM call. It's a deliberate design choice: a supervised
model trained on real historical ticket data predicts priority more
reliably and far cheaper than asking an LLM to guess from raw text.
"""

from graph.state import AegisOpsState

# TODO: load the actual trained model artifact, e.g.:
# import joblib
# _model = joblib.load("models/itsm_priority_xgboost.pkl")


def run_priority_predictor(state: AegisOpsState) -> dict:
    incident_text = state["incident_text"]

    # TODO: replace with real feature extraction + _model.predict_proba(...)
    predicted_priority = "P3"
    confidence = 0.0

    return {
        "predicted_priority": predicted_priority,
        "priority_confidence": confidence,
    }
