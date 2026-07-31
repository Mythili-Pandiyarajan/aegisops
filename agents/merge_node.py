"""
AegisOps Merge Node

Combines priority predictor and category classifier outputs.

Responsibilities:
- Evaluate prediction confidence
- Flag incidents requiring human review
- Escalate critical categories
"""

from graph.state import AegisOpsState


CONFIDENCE_THRESHOLD = 0.60


HIGH_RISK_CATEGORIES = {
    "security",
    "database",
}


def merge_priority_and_category(
    state: AegisOpsState
) -> dict:


    priority = state.get(
        "predicted_priority",
        "Unknown"
    )


    category = state.get(
        "predicted_category",
        ""
    ).lower()



    priority_conf = state.get(
        "priority_confidence",
        1.0
    )


    category_conf = state.get(
        "category_confidence",
        1.0
    )



    #################################################
    # Confidence based review
    #################################################

    low_confidence = (
        priority_conf < CONFIDENCE_THRESHOLD
        or category_conf < CONFIDENCE_THRESHOLD
    )



    #################################################
    # Critical escalation
    #################################################

    high_risk_category = (
        category in HIGH_RISK_CATEGORIES
    )


    critical_priority = (
        priority == "P1"
    )



    needs_review = (
        low_confidence
        or high_risk_category
        or critical_priority
    )



    print("==============================")
    print("MERGE NODE")
    print("==============================")
    print("Priority:", priority)
    print("Category:", category)
    print("Priority confidence:", priority_conf)
    print("Category confidence:", category_conf)
    print("Human review:", needs_review)



    return {

        "needs_human_review": needs_review,

    }
