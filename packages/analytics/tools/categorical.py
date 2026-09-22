"""Categorical summary tool using Polars."""
from __future__ import annotations
from typing import Optional
import polars as pl
from packages.analytics.tools.models import CategoricalStats


def describe_categorical(df: pl.DataFrame, column: str) -> Optional[CategoricalStats]:
    """Calculate unique counts and top value distribution for categorical/string columns.

    Args:
        df: Polars DataFrame.
        column: Column name.

    Returns:
        CategoricalStats or None if column is purely numeric.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    s = df[column]
    if s.dtype.is_numeric():
        return None

    unique_count = s.n_unique()
    null_count = s.null_count()

    # Top 5 value counts (excluding nulls)
    top_vc = (
        s.drop_nulls()
        .value_counts()
        .sort(by="count", descending=True)
        .head(5)
    )

    top_values = {
        str(row[0]): int(row[1])
        for row in top_vc.iter_rows()
    }

    return CategoricalStats(
        column=column,
        unique_count=int(unique_count),
        top_values=top_values,
        null_count=int(null_count),
    )
