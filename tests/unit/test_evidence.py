"""Unit tests for Evidence and Finding models, validation, and builders."""
import uuid
import pytest
from pydantic import ValidationError

from packages.evidence.models import Evidence, Finding
from packages.evidence.strength import (
    classify_correlation_strength,
    classify_outlier_strength,
    classify_missingness_strength,
    classify_skew_strength,
)
from packages.evidence.builders import (
    build_correlation_finding,
    build_outlier_finding,
    build_missingness_finding,
    build_distribution_finding,
)
from packages.analytics.tools.models import (
    CorrelationPair,
    OutlierResult,
    MissingnessStats,
    ColumnStats,
)


def test_finding_requires_non_empty_evidence():
    # Constructing a Finding with empty evidence list must raise ValidationError
    with pytest.raises(ValidationError):
        Finding(
            claim="Empty evidence test claim",
            evidence=[],
            evidence_strength="strong",
            dataset_version_id=uuid.uuid4(),
        )


def test_correlation_strength_boundaries():
    # Strong: |r| >= 0.70 and n >= 30
    assert classify_correlation_strength(r=0.70, n=30) == "strong"
    assert classify_correlation_strength(r=-0.85, n=50) == "strong"

    # Just below strong r threshold -> moderate
    assert classify_correlation_strength(r=0.699, n=30) == "moderate"

    # Just below strong n threshold -> moderate
    assert classify_correlation_strength(r=0.85, n=29) == "moderate"

    # Moderate: |r| >= 0.40 and n >= 15
    assert classify_correlation_strength(r=0.40, n=15) == "moderate"
    assert classify_correlation_strength(r=-0.45, n=20) == "moderate"

    # Below moderate -> weak
    assert classify_correlation_strength(r=0.39, n=20) == "weak"
    assert classify_correlation_strength(r=0.50, n=14) == "weak"

    # Sample too small (n <= 4) -> insufficient
    assert classify_correlation_strength(r=0.99, n=4) == "insufficient"
    assert classify_correlation_strength(r=1.00, n=1) == "insufficient"


def test_outlier_strength_boundaries():
    assert classify_outlier_strength(pct=15.0, count=10) == "strong"
    assert classify_outlier_strength(pct=5.0, count=10) == "moderate"
    assert classify_outlier_strength(pct=1.5, count=2) == "weak"
    assert classify_outlier_strength(pct=0.0, count=0) == "insufficient"


def test_missingness_strength_boundaries():
    assert classify_missingness_strength(pct=35.0, count=100) == "strong"
    assert classify_missingness_strength(pct=15.0, count=50) == "moderate"
    assert classify_missingness_strength(pct=2.0, count=5) == "weak"
    assert classify_missingness_strength(pct=0.0, count=0) == "insufficient"


def test_builders():
    d_id = uuid.uuid4()
    r_id = uuid.uuid4()

    # 1. Correlation Builder
    corr_pair = CorrelationPair(col_a="sales", col_b="profit", r=0.82, direction="positive")
    finding_corr = build_correlation_finding(corr_pair, n=100, dataset_version_id=d_id, analysis_run_id=r_id)
    assert finding_corr.evidence_strength == "strong"
    assert len(finding_corr.evidence) == 2
    assert finding_corr.source_columns == ["sales", "profit"]

    # 2. Outlier Builder
    outlier_res = OutlierResult(column="age", count=12, pct=12.5, lower_bound=0.0, upper_bound=80.0)
    finding_outlier = build_outlier_finding(outlier_res, dataset_version_id=d_id)
    assert finding_outlier.evidence_strength == "strong"
    assert len(finding_outlier.evidence) == 2

    # 3. Missingness Builder
    missing_stat = MissingnessStats(column="income", count=250, pct=25.0)
    finding_missing = build_missingness_finding(missing_stat, dataset_version_id=d_id)
    assert finding_missing.evidence_strength == "moderate"
    assert len(finding_missing.evidence) == 2

    # 4. Distribution Builder
    dist_stat = ColumnStats(
        column="charges",
        mean=500.0,
        median=200.0,
        std=150.0,
        min=10.0,
        max=5000.0,
        skew=2.45,
        null_count=0,
    )
    finding_dist = build_distribution_finding(dist_stat, dataset_version_id=d_id)
    assert finding_dist.evidence_strength == "strong"
    assert len(finding_dist.evidence) == 3
