"""Pairwise correlation calculation tool using Polars."""
from __future__ import annotations
from typing import List
import polars as pl
from packages.analytics.tools.models import CorrelationPair


def calculate_correlation(df: pl.DataFrame, limit: int = 10) -> List[CorrelationPair]:
    """Calculate top Pearson correlation pairs across numeric columns.

    Args:
        df: Polars DataFrame.
        limit: Max correlation pairs to return (default 10).

    Returns:
        List of CorrelationPair sorted descending by absolute r value.
    """
    numeric_cols = [col for col in df.columns if df[col].dtype.is_numeric()]
    if len(numeric_cols) < 2:
        return []

    pairs = []
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1:]:
            # Compute correlation on pairwise non-null rows
            sub_df = df.select([col_a, col_b]).drop_nulls()
            if len(sub_df) < 2:
                continue
            r_val = sub_df.select(pl.corr(col_a, col_b)).item()
            if r_val is not None and not (isinstance(r_val, float) and (r_val != r_val)):  # check not NaN
                pairs.append((col_a, col_b, round(float(r_val), 4)))

    pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    return [
        CorrelationPair(
            col_a=a,
            col_b=b,
            r=r,
            direction="positive" if r > 0 else "negative",
        )
        for a, b, r in pairs[:limit]
    ]
