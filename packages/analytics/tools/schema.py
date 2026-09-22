"""Schema inspection tool using Polars."""
from __future__ import annotations
from typing import List
import polars as pl
from packages.analytics.tools.models import ColumnSchema


def inspect_schema(df: pl.DataFrame) -> List[ColumnSchema]:
    """Inspect column names and data types of a DataFrame."""
    return [
        ColumnSchema(name=col, dtype=str(dtype))
        for col, dtype in zip(df.columns, df.dtypes)
    ]
