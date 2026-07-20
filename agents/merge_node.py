"""
Merge Node — combines the outputs of the parallel priority predictor
and category classifier into a single merged state before the rest of
the pipeline runs. Kept as its own explicit node (rather than folded
into the next agent) so the merge point is visible and testable on its
own — see tests/test_merge_node.py.
"""

from graph.state import AegisOpsState


def merge_priority_and_category(state: AegisOpsState) -> dict:
    # Both branches have already written their fields into state by the
    # time this node runs (LangGraph waits for all incoming edges).
    # This node exists to do any combined logic — e.g. flagging low
    # confidence on either branch for human review — rather than to
    # produce new fields on its own.

    low_confidence = (
        state.get("priority_confidence", 1.0) < 0.6
        or state.get("category_confidence", 1.0) < 0.6
    )

    return {
        "needs_human_review": low_confidence,
    }
