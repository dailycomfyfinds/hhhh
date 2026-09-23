from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class Destination:
    id: str
    market: str
    network: str
    url: str
    priority: int = 0
    active: bool = True

def choose_destination(destinations: list[Destination], market: str) -> Destination:
    candidates = [d for d in destinations if d.active and d.market in (market, "INTL") and urlparse(d.url).scheme in ("http", "https")]
    if not candidates:
        raise LookupError(f"no active affiliate destination for market {market}")
    return sorted(candidates, key=lambda d: (d.market != market, -d.priority))[0]
