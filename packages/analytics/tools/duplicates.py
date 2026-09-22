"""Duplicate row detection tool using Polars."""
from __future__ import annotations
import polars as pl
from packages.analytics.tools.models import DuplicateStats


def count_duplicate_rows(df: pl.DataFrame) -> DuplicateStats:
    """Calculate the number and percentage of duplicate rows in a DataFrame."""
    total_rows = len(df)
    if total_rows == 0:
        return DuplicateStats(duplicate_rows=0, pct=0.0)

    unique_rows = len(df.unique())
    duplicates = total_rows - unique_rows
    pct = round(duplicates / total_rows * 100, 2)

    return DuplicateStats(
        duplicate_rows=int(duplicates),
        pct=float(pct),
    )
