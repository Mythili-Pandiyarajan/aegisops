from agents.merge_node import merge_priority_and_category


def test_flags_low_confidence_for_review():
    state = {"priority_confidence": 0.4, "category_confidence": 0.9}
    result = merge_priority_and_category(state)
    assert result["needs_human_review"] is True


def test_does_not_flag_high_confidence():
    state = {"priority_confidence": 0.9, "category_confidence": 0.95}
    result = merge_priority_and_category(state)
    assert result["needs_human_review"] is False
