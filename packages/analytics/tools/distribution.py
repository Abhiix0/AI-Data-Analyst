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

    def _to_float(v: object) -> float:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v))

    std_num = _to_float(std_val)

    # Sample skewness (bias=False)
    if len(s_float) >= 3 and std_num > 0:
        try:
            skew_val = s_float.skew(bias=False)
        except TypeError:
            skew_val = s_float.skew()
    else:
        skew_val = 0.0

    return ColumnStats(
        column=column,
        mean=round(_to_float(mean_val), 4),
        median=round(_to_float(median_val), 4),
        std=round(std_num, 4),
        min=round(_to_float(min_val), 4),
        max=round(_to_float(max_val), 4),
        skew=round(_to_float(skew_val), 4),
        null_count=null_count,
    )
