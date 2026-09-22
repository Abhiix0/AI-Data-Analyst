"""Missingness calculation tool using Polars."""
from __future__ import annotations
from typing import Dict
import polars as pl
from packages.analytics.tools.models import MissingnessStats


def calculate_missingness(df: pl.DataFrame) -> Dict[str, MissingnessStats]:
    """Calculate missing value counts and percentages per column.

    Only returns columns with count > 0.

    Args:
        df: Polars DataFrame.

    Returns:
        Dict mapping column name to MissingnessStats.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {}

    missing_info: Dict[str, MissingnessStats] = {}
    for col in df.columns:
        null_count = df[col].null_count()
        if null_count > 0:
            pct = round(null_count / total_rows * 100, 2)
            missing_info[col] = MissingnessStats(
                column=col,
                count=int(null_count),
                pct=float(pct),
            )

    return missing_info
