"""Deterministic threshold constants for evidence strength classification.

All statistical confidence and finding strengths are derived from these
thresholds, encoding our 'no fabricated confidence' principle.
"""
from __future__ import annotations

# ── Correlation Thresholds ──────────────────────────────────────────
# Strong: High effect size (|r| >= 0.70) with adequate sample power (n >= 30)
CORRELATION_STRONG_R = 0.70
CORRELATION_STRONG_MIN_N = 30

# Moderate: Meaningful correlation (|r| >= 0.40) with baseline sample size (n >= 15)
CORRELATION_MODERATE_R = 0.40
CORRELATION_MODERATE_MIN_N = 15

# Insufficient: Too few observations (n < 5) to draw valid correlation inference regardless of r
CORRELATION_INSUFFICIENT_MAX_N = 4


# ── Outlier Severity Thresholds ─────────────────────────────────────
# Strong: Pervasive or extreme anomaly rate (> 10% of values are IQR outliers)
OUTLIER_STRONG_PCT = 10.0

# Moderate: Notable presence of outliers (2.0% - 10.0%)
OUTLIER_MODERATE_PCT = 2.0


# ── Missingness Severity Thresholds ──────────────────────────────────
# Strong / Critical: More than 30% missing values (requires dropping or heavy imputation)
MISSINGNESS_STRONG_PCT = 30.0

# Moderate: 5.0% - 30.0% missing (requires investigation before modeling)
MISSINGNESS_MODERATE_PCT = 5.0


# ── Skewness Thresholds ──────────────────────────────────────────────
# Strong / Heavy: |skew| >= 2.0 (highly asymmetric distribution, log-transform candidate)
SKEW_HEAVY = 2.0

# Moderate: 1.0 <= |skew| < 2.0 (moderately skewed)
SKEW_MODERATE = 1.0
