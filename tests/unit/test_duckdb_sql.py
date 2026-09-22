"""Unit tests for DuckDB query engine, SQL guardrails, and caching."""
import io
import os
import shutil
import tempfile
import polars as pl
import pytest

from packages.analytics.sql_guard import validate_and_sanitize_query, SqlValidationError
from packages.analytics.duckdb_engine import DuckDBEngine
from packages.analytics.tools.sql import run_sql, explain_sql
from packages.analytics.parquet_cache import ParquetCache
from packages.shared.storage import LocalDiskStorageClient


def test_sql_guard_allowlist():
    # Valid SELECT
    sanitized, _ = validate_and_sanitize_query("SELECT * FROM dataset")
    assert "LIMIT" in sanitized
    assert sanitized.startswith("SELECT * FROM dataset")

    # Valid WITH (CTE)
    cte_query = "WITH summary AS (SELECT category, COUNT(*) as cnt FROM dataset GROUP BY 1) SELECT * FROM summary"
    sanitized_cte, _ = validate_and_sanitize_query(cte_query)
    assert sanitized_cte.startswith("WITH")
    assert "LIMIT" in sanitized_cte


def test_sql_guard_disallowed_statements():
    disallowed = [
        "DROP TABLE dataset",
        "DELETE FROM dataset WHERE id = 1",
        "INSERT INTO dataset VALUES (1, 'bad')",
        "UPDATE dataset SET name = 'hacked'",
        "ALTER TABLE dataset DROP COLUMN id",
        "ATTACH 'evil.db' AS evil",
        "PRAGMA table_info('dataset')",
        "COPY dataset TO 'stolen.csv'",
        "SELECT * FROM dataset; DROP TABLE dataset",
    ]
    for bad_sql in disallowed:
        with pytest.raises(SqlValidationError):
            validate_and_sanitize_query(bad_sql)


def test_sql_guard_limit_clamping():
    # Enforces max limit
    sanitized, truncated = validate_and_sanitize_query("SELECT * FROM dataset LIMIT 50000", max_rows=1000)
    assert "LIMIT 1000" in sanitized
    assert truncated is True

    # Respects smaller limit
    sanitized_small, truncated_small = validate_and_sanitize_query("SELECT * FROM dataset LIMIT 50", max_rows=1000)
    assert "LIMIT 50" in sanitized_small
    assert truncated_small is False


def test_duckdb_execution_and_explain():
    temp_dir = tempfile.mkdtemp()
    try:
        parquet_file = os.path.join(temp_dir, "test.parquet")
        df = pl.DataFrame({
            "dept": ["Eng", "Eng", "Sales", "Sales", "HR"],
            "salary": [100000, 120000, 80000, 95000, 70000],
        })
        df.write_parquet(parquet_file)

        # 1. Run aggregation
        query = "SELECT dept, COUNT(*) as headcount, AVG(salary) as avg_sal FROM dataset GROUP BY dept ORDER BY avg_sal DESC"
        result = run_sql(parquet_path=parquet_file, sql=query)

        assert result.columns == ["dept", "headcount", "avg_sal"]
        assert len(result.rows) == 3
        assert result.rows[0][0] == "Eng"
        assert result.rows[0][1] == 2
        assert result.rows[0][2] == 110000.0
        assert result.truncated is False
        assert result.execution_time_ms >= 0

        # 2. Explain SQL
        plan = explain_sql(parquet_path=parquet_file, sql=query)
        assert len(plan) > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_parquet_cache():
    temp_dir = tempfile.mkdtemp()
    try:
        storage_dir = os.path.join(temp_dir, "storage")
        cache_dir = os.path.join(temp_dir, "cache")
        storage = LocalDiskStorageClient(base_dir=storage_dir)
        cache = ParquetCache(cache_dir=cache_dir, ttl_seconds=10)

        # Upload dummy parquet to storage
        key = "datasets/123/456/data.parquet"
        storage.upload_bytes(key, b"PAR1_DUMMY_DATA")

        # First fetch
        local_path_1 = cache.get_or_fetch(key, storage)
        assert os.path.isfile(local_path_1)

        # Second fetch hits cache
        local_path_2 = cache.get_or_fetch(key, storage)
        assert local_path_1 == local_path_2
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
