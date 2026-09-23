import pytest
from dcf_hq.evaluation import score_product
from dcf_hq.affiliate import Destination, choose_destination
from dcf_hq.content import format_for_platform
from dcf_hq.qa import run_quality_checks
from dcf_hq.publishing import can_publish, idempotency_key

def test_score_is_configurable():
    result = score_product({"usefulness": 1, "value": .5}, {"usefulness": .75, "value": .25})
    assert result.score == .875 and result.decision == "PASS"

def test_market_routing_prefers_exact_market():
    chosen = choose_destination([Destination("i", "INTL", "AliExpress", "https://a.test"), Destination("u", "US", "Amazon", "https://u.test", 1)], "US")
    assert chosen.id == "u"

def test_x_format_is_platform_specific():
    result = format_for_platform({"hook": "Useful find", "caption": "A compact idea", "cta": "See details", "disclosure": "#ad"}, "X")
    assert result["platform"] == "X" and len(result["text"]) <= 280

def test_qa_blocks_missing_approval_inputs():
    result = run_quality_checks({"product_id": "p", "market": "US", "cta": "See", "affiliate_destination": "bad", "disclosure_required": True})
    assert result.status == "BLOCKED"

def test_unapproved_publish_is_blocked():
    allowed, reason = can_publish({"approval_status": "PENDING", "qa_status": "PASS"})
    assert not allowed and "approval" in reason

def test_idempotency_is_stable():
    assert idempotency_key("j", "c", 1, "X") == idempotency_key("j", "c", 1, "X")
