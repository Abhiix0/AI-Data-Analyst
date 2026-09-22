"""Finding builder factories wiring tool outputs to typed Finding models."""
from __future__ import annotations
import uuid
from typing import Optional
from packages.evidence.models import Evidence, Finding
from packages.evidence.strength import (
    classify_correlation_strength,
    classify_outlier_strength,
    classify_missingness_strength,
    classify_skew_strength,
)
from packages.analytics.tools.models import (
    CorrelationPair,
    OutlierResult,
    MissingnessStats,
    ColumnStats,
)


def build_correlation_finding(
    pair: CorrelationPair,
    n: int,
    dataset_version_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
) -> Finding:
    """Construct a typed Finding for a correlation result."""
    strength = classify_correlation_strength(r=pair.r, n=n)
    evidence = [
        Evidence(
            metric_name="pearson_correlation",
            value=pair.r,
            source_tool="calculate_correlation",
            source_columns=[pair.col_a, pair.col_b],
        ),
        Evidence(
            metric_name="sample_size",
            value=n,
            source_tool="calculate_correlation",
            source_columns=[pair.col_a, pair.col_b],
        ),
    ]
    claim = (
        f"Columns '{pair.col_a}' and '{pair.col_b}' have a {strength} {pair.direction} "
        f"correlation (r={pair.r:.4f}, n={n})."
    )
    return Finding(
        claim=claim,
        evidence=evidence,
        evidence_strength=strength,
        dataset_version_id=dataset_version_id,
        analysis_run_id=analysis_run_id,
        source_columns=[pair.col_a, pair.col_b],
        query=f"calculate_correlation('{pair.col_a}', '{pair.col_b}')",
    )


def build_outlier_finding(
    outlier: OutlierResult,
    dataset_version_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
) -> Finding:
    """Construct a typed Finding for an IQR outlier detection result."""
    strength = classify_outlier_strength(pct=outlier.pct, count=outlier.count)
    evidence = [
        Evidence(
            metric_name="outlier_count",
            value=outlier.count,
            source_tool="detect_outliers",
            source_columns=[outlier.column],
        ),
        Evidence(
            metric_name="outlier_pct",
            value=outlier.pct,
            source_tool="detect_outliers",
            source_columns=[outlier.column],
        ),
    ]
    claim = (
        f"Column '{outlier.column}' exhibits {strength} outlier presence with {outlier.count} "
        f"values ({outlier.pct:.2f}%) outside IQR bounds [{outlier.lower_bound}, {outlier.upper_bound}]."
    )
    return Finding(
        claim=claim,
        evidence=evidence,
        evidence_strength=strength,
        dataset_version_id=dataset_version_id,
        analysis_run_id=analysis_run_id,
        source_columns=[outlier.column],
        query=f"detect_outliers('{outlier.column}')",
    )


def build_missingness_finding(
    missing: MissingnessStats,
    dataset_version_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
) -> Finding:
    """Construct a typed Finding for a missingness result."""
    strength = classify_missingness_strength(pct=missing.pct, count=missing.count)
    evidence = [
        Evidence(
            metric_name="missing_count",
            value=missing.count,
            source_tool="calculate_missingness",
            source_columns=[missing.column],
        ),
        Evidence(
            metric_name="missing_pct",
            value=missing.pct,
            source_tool="calculate_missingness",
            source_columns=[missing.column],
        ),
    ]
    claim = (
        f"Column '{missing.column}' has {strength} data quality impact with {missing.count:,} "
        f"missing values ({missing.pct:.2f}% null)."
    )
    return Finding(
        claim=claim,
        evidence=evidence,
        evidence_strength=strength,
        dataset_version_id=dataset_version_id,
        analysis_run_id=analysis_run_id,
        source_columns=[missing.column],
        query=f"calculate_missingness('{missing.column}')",
    )


def build_distribution_finding(
    stat: ColumnStats,
    dataset_version_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
) -> Finding:
    """Construct a typed Finding for a numeric distribution result."""
    strength = classify_skew_strength(skew=stat.skew)
    direction = "right" if stat.skew > 0 else "left"
    evidence = [
        Evidence(
            metric_name="skewness",
            value=stat.skew,
            source_tool="describe_column",
            source_columns=[stat.column],
        ),
        Evidence(
            metric_name="mean",
            value=stat.mean,
            source_tool="describe_column",
            source_columns=[stat.column],
        ),
        Evidence(
            metric_name="median",
            value=stat.median,
            source_tool="describe_column",
            source_columns=[stat.column],
        ),
    ]
    claim = (
        f"Column '{stat.column}' has {strength} {direction}-skew (skew={stat.skew:.2f}) "
        f"with mean={stat.mean:.2f} and median={stat.median:.2f}."
    )
    return Finding(
        claim=claim,
        evidence=evidence,
        evidence_strength=strength,
        dataset_version_id=dataset_version_id,
        analysis_run_id=analysis_run_id,
        source_columns=[stat.column],
        query=f"describe_column('{stat.column}')",
    )
