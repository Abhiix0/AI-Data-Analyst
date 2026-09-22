"""Anomaly detection tool combining Z-score and IQR methods in Polars."""
from __future__ import annotations
from typing import List
import polars as pl
from packages.analytics.tools.models import AnomalyResult


def find_anomalies(
    df: pl.DataFrame,
    column: str,
    method: str = "zscore",
    threshold: float = 3.0,
    limit: int = 20,
) -> AnomalyResult:
    """Find anomalies in a numeric column using Z-score or IQR thresholds.

    Args:
        df: Polars DataFrame.
        column: Numeric column name.
        method: 'zscore' or 'iqr'.
        threshold: Z-score cutoff (default 3.0 standard deviations).
        limit: Max sampled anomaly records to return (capped at 50).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    s = df[column].drop_nulls()
    if not s.dtype.is_numeric() or len(s) < 5:
        return AnomalyResult(
            column=column,
            method=method,
            anomaly_count=0,
            anomaly_pct=0.0,
            sample_anomalies=[],
        )

    s_float = s.cast(pl.Float64)
    total_non_null = len(s_float)

    if method == "iqr":
        q1 = s_float.quantile(0.25, interpolation="linear") or 0.0
        q3 = s_float.quantile(0.75, interpolation="linear") or 0.0
        iqr = q3 - q1
        lo = q1 - 1.5 * iqr
        hi = q3 + 1.5 * iqr
        anomaly_df = df.filter((pl.col(column) < lo) | (pl.col(column) > hi))
    else:
        # Default: Z-score
        mean_val = s_float.mean() or 0.0
        std_val = s_float.std() or 1.0
        if std_val == 0:
            return AnomalyResult(
                column=column,
                method="zscore",
                anomaly_count=0,
                anomaly_pct=0.0,
                sample_anomalies=[],
            )
        z_expr = (pl.col(column).cast(pl.Float64) - mean_val).abs() / std_val
        anomaly_df = df.filter(z_expr > threshold)

    anomaly_count = len(anomaly_df)
    anomaly_pct = round(anomaly_count / total_non_null * 100, 2)

    safe_limit = min(max(1, limit), 50)
    sample_records = anomaly_df.head(safe_limit).to_dicts()

    return AnomalyResult(
        column=column,
        method=method,
        anomaly_count=int(anomaly_count),
        anomaly_pct=float(anomaly_pct),
        sample_anomalies=sample_records,
    )
