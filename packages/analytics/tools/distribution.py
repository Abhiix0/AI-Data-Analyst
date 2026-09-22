"""Numeric column distribution tool using Polars."""
from __future__ import annotations
from typing import Optional
import polars as pl
from packages.analytics.tools.models import ColumnStats


def describe_column(df: pl.DataFrame, column: str) -> Optional[ColumnStats]:
    """Calculate summary statistics for a numeric column.

    Computes mean, median, std, min, max, skew, null_count rounded to 4 decimal places.

    Args:
        df: Polars DataFrame.
        column: Column name.

    Returns:
        ColumnStats or None if column is non-numeric or completely empty.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    s = df[column].drop_nulls()
    null_count = df[column].null_count()

    if not s.dtype.is_numeric() or len(s) == 0:
        return None

    # Cast to float for calculation
    s_float = s.cast(pl.Float64)
    mean_val = s_float.mean()
    median_val = s_float.median()
    std_val = s_float.std() if len(s_float) > 1 else 0.0
    min_val = s_float.min()
    max_val = s_float.max()

    # Sample skewness (bias=False)
    if len(s_float) >= 3 and std_val is not None and std_val > 0:
        try:
            skew_val = s_float.skew(bias=False)
        except TypeError:
            skew_val = s_float.skew()
    else:
        skew_val = 0.0

    return ColumnStats(
        column=column,
        mean=round(float(mean_val if mean_val is not None else 0.0), 4),
        median=round(float(median_val if median_val is not None else 0.0), 4),
        std=round(float(std_val if std_val is not None else 0.0), 4),
        min=round(float(min_val if min_val is not None else 0.0), 4),
        max=round(float(max_val if max_val is not None else 0.0), 4),
        skew=round(float(skew_val if skew_val is not None else 0.0), 4),
        null_count=int(null_count),
    )
