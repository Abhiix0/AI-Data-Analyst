"""Deterministic evidence strength classification functions."""
from __future__ import annotations
from typing import Literal
from packages.evidence.thresholds import (
    CORRELATION_STRONG_R,
    CORRELATION_STRONG_MIN_N,
    CORRELATION_MODERATE_R,
    CORRELATION_MODERATE_MIN_N,
    CORRELATION_INSUFFICIENT_MAX_N,
    OUTLIER_STRONG_PCT,
    OUTLIER_MODERATE_PCT,
    MISSINGNESS_STRONG_PCT,
    MISSINGNESS_MODERATE_PCT,
    SKEW_HEAVY,
    SKEW_MODERATE,
)

EvidenceStrength = Literal["strong", "moderate", "weak", "insufficient"]


def classify_correlation_strength(r: float, n: int) -> EvidenceStrength:
    """Classify the statistical strength of a correlation finding based on |r| and sample size n."""
    if n <= CORRELATION_INSUFFICIENT_MAX_N:
        return "insufficient"

    abs_r = abs(r)
    if abs_r >= CORRELATION_STRONG_R and n >= CORRELATION_STRONG_MIN_N:
        return "strong"
    if abs_r >= CORRELATION_MODERATE_R and n >= CORRELATION_MODERATE_MIN_N:
        return "moderate"
    return "weak"


def classify_outlier_strength(pct: float, count: int) -> EvidenceStrength:
    """Classify outlier severity based on percentage and count."""
    if count == 0:
        return "insufficient"
    if pct >= OUTLIER_STRONG_PCT and count >= 5:
        return "strong"
    if pct >= OUTLIER_MODERATE_PCT:
        return "moderate"
    return "weak"


def classify_missingness_strength(pct: float, count: int) -> EvidenceStrength:
    """Classify missingness severity based on percentage."""
    if count == 0:
        return "insufficient"
    if pct >= MISSINGNESS_STRONG_PCT:
        return "strong"
    if pct >= MISSINGNESS_MODERATE_PCT:
        return "moderate"
    return "weak"


def classify_skew_strength(skew: float) -> EvidenceStrength:
    """Classify distribution skewness strength."""
    abs_skew = abs(skew)
    if abs_skew >= SKEW_HEAVY:
        return "strong"
    if abs_skew >= SKEW_MODERATE:
        return "moderate"
    return "weak"
