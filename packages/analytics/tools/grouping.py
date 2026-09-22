"""Group by and aggregation tools using Polars."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import polars as pl
from packages.analytics.tools.models import GroupByResult, AggregateResult


def group_by(
    df: pl.DataFrame,
    group_column: str,
    agg_column: str,
    agg_fn: str = "mean",
    limit: int = 50,
) -> GroupByResult:
    """Group by a categorical column and aggregate a numeric column.

    Supported agg_fn: 'mean', 'sum', 'count', 'min', 'max', 'median', 'std'.
    """
    if group_column not in df.columns:
        raise ValueError(f"Group column '{group_column}' not found.")
    if agg_column not in df.columns:
        raise ValueError(f"Agg column '{agg_column}' not found.")

    col = pl.col(agg_column)
    agg_fn_lower = agg_fn.lower()

    if agg_fn_lower == "mean":
        expr = col.mean()
    elif agg_fn_lower == "sum":
        expr = col.sum()
    elif agg_fn_lower == "count":
        expr = col.count()
    elif agg_fn_lower == "min":
        expr = col.min()
    elif agg_fn_lower == "max":
        expr = col.max()
    elif agg_fn_lower == "median":
        expr = col.median()
    elif agg_fn_lower == "std":
        expr = col.std()
    else:
        raise ValueError(f"Unsupported agg_fn '{agg_fn}'. Allowed: mean, sum, count, min, max, median, std")

    res_df = (
        df.group_by(group_column)
        .agg(expr.alias("val"))
        .sort("val", descending=True)
        .head(limit)
    )

    groups = [
        {"group": str(row[0]), "value": round(float(row[1]), 4) if row[1] is not None else None}
        for row in res_df.iter_rows()
    ]

    return GroupByResult(
        group_column=group_column,
        agg_column=agg_column,
        agg_fn=agg_fn,
        groups=groups,
    )


def aggregate(
    df: pl.DataFrame,
    column: str,
    agg_fn: str = "mean",
) -> AggregateResult:
    """Compute a single scalar aggregate metric over a column."""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    col = pl.col(column)
    agg_fn_lower = agg_fn.lower()

    if agg_fn_lower == "mean":
        expr = col.mean()
    elif agg_fn_lower == "sum":
        expr = col.sum()
    elif agg_fn_lower == "count":
        expr = col.count()
    elif agg_fn_lower == "min":
        expr = col.min()
    elif agg_fn_lower == "max":
        expr = col.max()
    elif agg_fn_lower == "median":
        expr = col.median()
    elif agg_fn_lower == "std":
        expr = col.std()
    else:
        raise ValueError(f"Unsupported agg_fn '{agg_fn}'. Allowed: mean, sum, count, min, max, median, std")

    val = df.select(expr).item()
    return AggregateResult(
        column=column,
        agg_fn=agg_fn,
        value=round(float(val), 4) if val is not None else None,
    )
