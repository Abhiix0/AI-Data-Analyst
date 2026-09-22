"""Dataset filtering analytics tool using Polars."""
from __future__ import annotations
from typing import Any, List
import polars as pl
from packages.analytics.tools.models import FilterResult


def filter_dataset(
    df: pl.DataFrame,
    column: str,
    operator: str,
    value: Any,
    limit: int = 50,
) -> FilterResult:
    """Filter dataset on a single condition and return match metrics and capped sample records.

    Supported operators: '==', '!=', '>', '>=', '<', '<=', 'contains'.

    Args:
        df: Polars DataFrame.
        column: Column name to filter.
        operator: Comparison operator.
        value: Target filter value.
        limit: Max sampled records to return (capped at 50).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    total_rows = len(df)
    col = pl.col(column)

    if operator in ("==", "eq", "="):
        cond = col == value
    elif operator in ("!=", "neq"):
        cond = col != value
    elif operator in (">", "gt"):
        cond = col > value
    elif operator in (">=", "gte"):
        cond = col >= value
    elif operator in ("<", "lt"):
        cond = col < value
    elif operator in ("<=", "lte"):
        cond = col <= value
    elif operator in ("contains", "like"):
        cond = col.cast(pl.String).str.contains(str(value))
    else:
        raise ValueError(f"Unsupported filter operator '{operator}'. Allowed: ==, !=, >, >=, <, <=, contains")

    filtered_df = df.filter(cond)
    matched_rows = len(filtered_df)
    matched_pct = round(matched_rows / total_rows * 100, 2) if total_rows > 0 else 0.0

    safe_limit = min(max(1, limit), 50)
    sampled_records = filtered_df.head(safe_limit).to_dicts()

    return FilterResult(
        column=column,
        operator=operator,
        value=value,
        total_rows=int(total_rows),
        matched_rows=int(matched_rows),
        matched_pct=float(matched_pct),
        sampled_records=sampled_records,
    )
