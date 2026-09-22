"""Column metadata, distinct values, and sample row inspection tools."""
from __future__ import annotations
from typing import Any, List
import polars as pl
from packages.analytics.tools.models import ColumnMetadata, UniqueValuesResult, SampleRowsResult


def get_column_metadata(df: pl.DataFrame, column: str) -> ColumnMetadata:
    """Retrieve metadata, data type, null count, and cardinality for a column."""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    s = df[column]
    return ColumnMetadata(
        column=column,
        dtype=str(s.dtype),
        null_count=int(s.null_count()),
        unique_count=int(s.n_unique()),
    )


def get_unique_values(df: pl.DataFrame, column: str, limit: int = 50) -> UniqueValuesResult:
    """Retrieve distinct non-null values for a column, capped at limit."""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    safe_limit = min(max(1, limit), 100)
    s = df[column].drop_nulls()
    unique_series = s.unique()
    total_unique = len(unique_series)
    values = unique_series.head(safe_limit).to_list()

    return UniqueValuesResult(
        column=column,
        total_unique=int(total_unique),
        values=values,
    )


def get_sample_rows(df: pl.DataFrame, n: int = 10) -> SampleRowsResult:
    """Retrieve a representative sample of records from the dataset, capped at 50."""
    total_rows = len(df)
    safe_n = min(max(1, n), 50)
    sample_df = df.head(safe_n)

    records = sample_df.to_dicts()
    return SampleRowsResult(
        total_rows=int(total_rows),
        sample_count=len(records),
        records=records,
    )
