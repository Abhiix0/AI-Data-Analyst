"""Outlier detection tool using IQR method in Polars."""
from __future__ import annotations
from typing import Optional
import polars as pl
from packages.analytics.tools.models import OutlierResult


def detect_outliers(df: pl.DataFrame, column: str) -> Optional[OutlierResult]:
    """Detect outliers in a numeric column using the Interquartile Range (IQR) method.

    Enforces minimum 10 non-null values threshold.

    Args:
        df: Polars DataFrame.
        column: Numeric column name.

    Returns:
        OutlierResult if outliers exist and column has >=10 values, else None.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    s = df[column].drop_nulls()
    if not s.dtype.is_numeric() or len(s) < 10:
        return None

    s_float = s.cast(pl.Float64)
    q1 = s_float.quantile(0.25, interpolation="linear")
    q3 = s_float.quantile(0.75, interpolation="linear")

    if q1 is None or q3 is None:
        return None

    iqr = q3 - q1
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr

    outlier_count = s_float.filter((s_float < lo) | (s_float > hi)).len()
    if outlier_count == 0:
        return None

    pct = round(outlier_count / len(s) * 100, 2)

    return OutlierResult(
        column=column,
        count=int(outlier_count),
        pct=float(pct),
        lower_bound=round(float(lo), 4),
        upper_bound=round(float(hi), 4),
    )
