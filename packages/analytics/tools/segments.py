"""Segment comparison analytics tool using Polars."""
from __future__ import annotations
from typing import Dict
import polars as pl
from packages.analytics.tools.models import SegmentComparisonResult


def compare_segments(
    df: pl.DataFrame,
    segment_column: str,
    metric_column: str,
) -> SegmentComparisonResult:
    """Compare distribution metrics (mean, median, std, min, max, count) across segments."""
    if segment_column not in df.columns:
        raise ValueError(f"Segment column '{segment_column}' not found.")
    if metric_column not in df.columns:
        raise ValueError(f"Metric column '{metric_column}' not found.")

    col = pl.col(metric_column)
    grouped = df.group_by(segment_column).agg([
        pl.len().alias("count"),
        col.mean().alias("mean"),
        col.median().alias("median"),
        col.std().alias("std"),
        col.min().alias("min"),
        col.max().alias("max"),
    ])

    segments: Dict[str, Dict[str, float]] = {}
    for row in grouped.iter_rows(named=True):
        seg_name = str(row[segment_column])
        segments[seg_name] = {
            "count": float(row["count"]),
            "mean": round(float(row["mean"] or 0.0), 4),
            "median": round(float(row["median"] or 0.0), 4),
            "std": round(float(row["std"] or 0.0), 4),
            "min": round(float(row["min"] or 0.0), 4),
            "max": round(float(row["max"] or 0.0), 4),
        }

    return SegmentComparisonResult(
        segment_column=segment_column,
        metric_column=metric_column,
        segments=segments,
    )
