from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class QAResult:
    status: str
    issues: tuple[str, ...]

def run_quality_checks(asset: dict, platform_limit: int = 280) -> QAResult:
    blocked: list[str] = []
    warnings: list[str] = []
    if not asset.get("product_id"): blocked.append("missing product")
    if not asset.get("market"): blocked.append("missing market")
    if not asset.get("cta"): blocked.append("missing CTA")
    destination = asset.get("affiliate_destination")
    if not destination or urlparse(destination).scheme not in ("http", "https"): blocked.append("invalid affiliate destination")
    if asset.get("disclosure_required") and not asset.get("disclosure"): blocked.append("missing disclosure")
    text = asset.get("caption") or asset.get("body") or ""
    if len(text) > platform_limit: blocked.append("content exceeds platform limit")
    if asset.get("unsupported_claims"): blocked.append("unsupported claims")
    if asset.get("duplicate_fingerprint"): blocked.append("duplicate content")
    if not asset.get("media_reference"): warnings.append("media not attached")
    if blocked: return QAResult("BLOCKED", tuple(blocked + warnings))
    return QAResult("WARNING" if warnings else "PASS", tuple(warnings))
