from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalDecision:
    status: str
    reason: str


def can_approve_content(content: dict) -> ApprovalDecision:
    if content.get("qa_status") == "BLOCKED":
        return ApprovalDecision("BLOCKED", "QA blocked publishing")
    if not content.get("product_id"):
        return ApprovalDecision("BLOCKED", "missing product reference")
    if not content.get("market"):
        return ApprovalDecision("BLOCKED", "missing market")
    if not content.get("cta"):
        return ApprovalDecision("BLOCKED", "missing CTA")
    if not content.get("affiliate_destination"):
        return ApprovalDecision("BLOCKED", "missing affiliate destination")
    return ApprovalDecision("READY", "eligible for approval")


def enforce_approval_state(content: dict, approval_status: str | None) -> ApprovalDecision:
    decision = can_approve_content(content)
    if decision.status != "READY":
        return decision
    if approval_status != "APPROVED":
        return ApprovalDecision("BLOCKED", "explicit human approval required")
    return ApprovalDecision("APPROVED", "content approved")


def lifecycle_transition(current: str, target: str) -> bool:
    allowed = {
        "DISCOVERED": {"EVALUATED", "REJECTED", "BLOCKED"},
        "EVALUATED": {"CONTENT_GENERATED", "REJECTED", "BLOCKED"},
        "CONTENT_GENERATED": {"QA", "REJECTED", "BLOCKED"},
        "QA": {"READY_FOR_APPROVAL", "REJECTED", "BLOCKED", "HELD"},
        "READY_FOR_APPROVAL": {"APPROVED", "REJECTED", "HELD"},
        "APPROVED": {"SCHEDULED", "REJECTED", "HELD"},
        "SCHEDULED": {"SUBMITTED", "CANCELLED"},
        "SUBMITTED": {"PUBLISHED", "FAILED", "CANCELLED"},
        "PUBLISHED": {"TRACKING", "CANCELLED"},
        "TRACKING": {"ANALYZED", "CANCELLED"},
        "ANALYZED": {"OPTIMIZED", "CANCELLED"},
    }
    return target in allowed.get(current, set())
