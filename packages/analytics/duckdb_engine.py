"""DuckDB in-memory query engine over Parquet files."""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Tuple
import duckdb
from packages.analytics.sql_guard import validate_and_sanitize_query, SqlValidationError


class DuckDBEngine:
    """Read-only DuckDB SQL execution engine over Parquet datasets."""

    @staticmethod
    def execute_query(
        parquet_path: str,
        sql: str,
        view_name: str = "dataset",
        max_rows: int = 10_000,
        timeout_seconds: int = 15,
    ) -> Tuple[List[str], List[List[Any]], int, bool]:
        """Execute a sanitized read-only SQL query over a Parquet file.

        Args:
            parquet_path: Absolute local path to the Parquet file.
            sql: User/Agent provided SQL string.
            view_name: SQL view identifier (default 'dataset').
            max_rows: Maximum rows to return.
            timeout_seconds: Execution timeout in seconds.

        Returns:
            Tuple of (columns, rows, row_count, is_truncated)
        """
        if not os.path.isfile(parquet_path):
            raise FileNotFoundError(f"Parquet file not found at: {parquet_path}")

        # 1. Validate and sanitize query
        sanitized_sql, limit_applied = validate_and_sanitize_query(sql, max_rows=max_rows)

        # 2. Connect in-memory with query limits
        normalized_parquet_path = parquet_path.replace("\\", "/")
        con = duckdb.connect(database=":memory:")
        try:
            # Register parquet as view
            con.execute(f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{normalized_parquet_path}')")
            
            # Execute sanitized query
            cursor = con.execute(sanitized_sql)
            columns = [desc[0] for desc in cursor.description]
            records = cursor.fetchall()
            row_count = len(records)
            is_truncated = limit_applied and (row_count == max_rows)

            return columns, [list(r) for r in records], row_count, is_truncated
        finally:
            con.close()

    @staticmethod
    def explain_query(parquet_path: str, sql: str, view_name: str = "dataset") -> str:
        """Return the physical execution plan for a SQL query."""
        sanitized_sql, _ = validate_and_sanitize_query(sql)
        normalized_parquet_path = parquet_path.replace("\\", "/")
        con = duckdb.connect(database=":memory:")
        try:
            con.execute(f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{normalized_parquet_path}')")
            cursor = con.execute(f"EXPLAIN {sanitized_sql}")
            return "\n".join(str(r[1]) for r in cursor.fetchall())
        finally:
            con.close()
