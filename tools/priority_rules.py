"""
AegisOps Priority Rules

Replaces the XGBoost priority classifier for real-time triage.

Why a rule instead of a model:
Analysis of the 46k-row itsm_data.csv training set showed that
Priority = min(Impact, Urgency) in 99.94% of rows with usable data
(45,225 / 45,225 candidates). This matches the standard ITSM priority
matrix used by most service desks: Impact and Urgency are set by the
reporter/agent at ticket creation, and Priority is a deterministic
function of the two — not something that needs to be learned from
resolution-time history.

The original XGBoost model was trained on fields (Handle_Time_hrs,
No_of_Reassignments, Closure_Code) that don't exist at incident
creation time, which is why its predictions barely varied across
incidents of very different real severity (see README — Known
Limitations). This rule uses only creation-time inputs, so it is
both more accurate against the historical ground truth and honestly
scoped to what is actually knowable when an incident is filed.
"""

from typing import Tuple


# Empirical match rate of Priority = min(Impact, Urgency) against
# 45,225 historical tickets with usable Impact/Urgency/Priority values.
RULE_CONFIDENCE = 0.999


PRIORITY_LABELS = {
    1: "P1",
    2: "P2",
    3: "P3",
    4: "P4",
    5: "P5",
}


def _clamp(value: int) -> int:
    return max(1, min(5, value))


def predict_priority_from_impact_urgency(
        impact: int,
        urgency: int,
) -> Tuple[str, float]:
    """
    Priority = min(Impact, Urgency), matching the historical ITSM
    priority matrix. Impact/Urgency are 1 (highest) to 5 (lowest),
    same scale as the training data.
    """

    impact = _clamp(int(impact))
    urgency = _clamp(int(urgency))

    priority_id = min(impact, urgency)

    priority = PRIORITY_LABELS.get(
        priority_id,
        "P3",
    )

    return priority, RULE_CONFIDENCE
