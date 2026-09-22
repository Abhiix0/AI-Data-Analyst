"""SQL execution tool for agent and API queries."""
from __future__ import annotations
import time
from typing import Any, List
from pydantic import BaseModel, Field
from packages.analytics.duckdb_engine import DuckDBEngine


class QueryResult(BaseModel):
    """Result of an executed SQL query."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    truncated: bool
    execution_time_ms: float


def run_sql(
    parquet_path: str,
    sql: str,
    max_rows: int = 10_000,
    timeout_seconds: int = 15,
) -> QueryResult:
    """Execute a validated SQL query against a Parquet dataset.

    Args:
        parquet_path: Local path to Parquet file.
        sql: SQL query string (SELECT / WITH only).
        max_rows: Maximum rows allowed (default 10,000).
        timeout_seconds: Query timeout limit.

    Returns:
        QueryResult with column headers, row records, and truncation metadata.
    """
    start_time = time.perf_counter()
    columns, rows, count, truncated = DuckDBEngine.execute_query(
        parquet_path=parquet_path,
        sql=sql,
        max_rows=max_rows,
        timeout_seconds=timeout_seconds,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    return QueryResult(
        columns=columns,
        rows=rows,
        row_count=count,
        truncated=truncated,
        execution_time_ms=round(duration_ms, 2),
    )


def explain_sql(parquet_path: str, sql: str) -> str:
    """Get the DuckDB EXPLAIN execution plan for a query."""
    return DuckDBEngine.explain_query(parquet_path=parquet_path, sql=sql)
