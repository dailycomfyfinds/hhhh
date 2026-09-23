from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class Evaluation:
    dimensions: dict[str, float]
    score: float
    decision: str

def score_product(values: Mapping[str, float], weights: Mapping[str, float], minimum: float = 0.6) -> Evaluation:
    if not weights or abs(sum(weights.values()) - 1.0) > 0.001:
        raise ValueError("evaluation weights must sum to 1")
    missing = set(weights) - set(values)
    if missing:
        raise ValueError(f"missing evaluation dimensions: {sorted(missing)}")
    if any(not 0 <= float(values[k]) <= 1 for k in weights):
        raise ValueError("evaluation dimensions must be between 0 and 1")
    score = round(sum(float(values[k]) * float(weights[k]) for k in weights), 4)
    return Evaluation(dict(values), score, "PASS" if score >= minimum else "REVIEW")
