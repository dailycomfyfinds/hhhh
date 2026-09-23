from __future__ import annotations
import hashlib

def idempotency_key(job_id: str, content_id: str, version: int, platform: str, action: str = "publish") -> str:
    raw = f"{job_id}:{content_id}:{version}:{platform.upper()}:{action}"
    return hashlib.sha256(raw.encode()).hexdigest()

def can_publish(job: dict) -> tuple[bool, str]:
    if job.get("status") in {"PUBLISHED", "SUBMITTED"} or job.get("external_post_id"):
        return False, "already submitted or published"
    if job.get("approval_status") != "APPROVED":
        return False, "explicit human approval is required"
    if job.get("qa_status") == "BLOCKED":
        return False, "QA blocked publishing"
    return True, "ready"
