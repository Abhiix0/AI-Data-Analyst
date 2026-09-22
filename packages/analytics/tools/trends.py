"""Time-series and sequential trend detection tool using Polars."""
from __future__ import annotations
import polars as pl
from packages.analytics.tools.models import TrendResult


def find_trends(
    df: pl.DataFrame,
    time_column: str,
    metric_column: str,
) -> TrendResult:
    """Analyze temporal direction, rate of change, and slope for a metric column over time."""
    if time_column not in df.columns:
        raise ValueError(f"Time column '{time_column}' not found.")
    if metric_column not in df.columns:
        raise ValueError(f"Metric column '{metric_column}' not found.")

    sub_df = df.select([time_column, metric_column]).drop_nulls().sort(time_column)
    if len(sub_df) < 2:
        raise ValueError("Need at least 2 non-null records to compute a trend.")

    metrics = sub_df[metric_column].cast(pl.Float64).to_list()
    start_val = metrics[0]
    end_val = metrics[-1]
    n = len(metrics)

    # Calculate simple linear slope: y = mx + c
    x = list(range(n))
    mean_x = sum(x) / n
    mean_y = sum(metrics) / n

    denom = sum((xi - mean_x) ** 2 for xi in x)
    if denom != 0:
        slope = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, metrics)) / denom
    else:
        slope = 0.0

    pct_change = ((end_val - start_val) / abs(start_val) * 100.0) if start_val != 0 else 0.0

    if slope > 0.05 and pct_change > 2.0:
        direction = "increasing"
    elif slope < -0.05 and pct_change < -2.0:
        direction = "decreasing"
    else:
        direction = "stable"

    return TrendResult(
        time_column=time_column,
        metric_column=metric_column,
        direction=direction,
        slope=round(float(slope), 4),
        start_value=round(float(start_val), 4),
        end_value=round(float(end_val), 4),
        pct_change=round(float(pct_change), 2),
    )
