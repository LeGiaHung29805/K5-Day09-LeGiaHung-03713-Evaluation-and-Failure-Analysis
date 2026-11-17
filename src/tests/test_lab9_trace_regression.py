"""Reproduce the first wrong decision and isolate the FM-08 grader."""

import pytest

pytestmark = pytest.mark.student


def test_ticket_delay_cannot_replace_database_fact():
    from lab9.trace_case import investigate

    broken = investigate("seeded_regression", "C-002", 11)["trial"]
    fixed = investigate("fixed", "C-002", 11)["trial"]
    assert broken["events"][2]["kind"] == "model_override"
    assert broken["snapshot"]["refund_vnd"] == 20_000
    assert not broken["lab8_pass"]
    assert all(event["kind"] != "model_override" for event in fixed["events"])
    assert fixed["snapshot"]["refund_vnd"] == 0
    assert fixed["lab8_pass"]


def test_reply_amount_compared_with_committed_refund(monkeypatch):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab8.shapes import SHAPES
    from lab9.graders import ReplyLedgerMatch
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    shape = "test_misreport"
    monkeypatch.setitem(SHAPES, shape, make_shape(shape, {"no_override", "misreport"}))
    for candidate, expected in ((shape, False), ("fixed", True)):
        case = investigate(candidate, "C-008", 11)
        assert case["trial"]["lab8_pass"]
        context = EvaluatorContext(name="C-008@11", inputs={}, metadata=None,
                                   expected_output=case["label"], output=case["trial"],
                                   duration=0.0, _span_tree=None, attributes={}, metrics={})
        assert ReplyLedgerMatch().evaluate(context).value is expected
