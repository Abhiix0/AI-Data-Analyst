# DuckDB Query Engine & SQL Guardrails

## Overview
The `packages/analytics` layer incorporates DuckDB as an embedded analytical SQL engine capable of querying Parquet files with vectorized execution speed, zero server overhead, and strict security guardrails.

```text
User / Agent Query ("SELECT category, AVG(sales) FROM dataset GROUP BY 1")
                                 │
                                 ▼
                     [packages.analytics.sql_guard]
                     • Allowlist Check: SELECT or WITH (CTE) only
                     • Statement Stacking Check: No multi-statement injection
                     • Disallowed Keyword Rejection: DROP, DELETE, INSERT, ATTACH, etc.
                     • Automatic LIMIT Injection & Clamping (<= 10,000 rows)
                                 │
                                 ▼
                     [packages.analytics.duckdb_engine]
                     • In-memory temporary connection (`:memory:`)
                     • Parquet view registration (`CREATE VIEW dataset AS ...`)
                     • Parameterized query execution & timeout protection
                                 │
                                 ▼
                     [QueryResult Pydantic Model]
                     • columns: List[str]
                     • rows: List[List[Any]]
                     • row_count: int
                     • truncated: bool
                     • execution_time_ms: float
```

## Security Guardrails

### 1. Statement Restriction
Queries must begin with `SELECT` or `WITH`. Any attempt to execute DDL, DML, or administrative commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `ATTACH`, `DETACH`, `COPY`, `PRAGMA`, `LOAD`, `INSTALL`) is rejected immediately with a `SqlValidationError`.

### 2. Multi-Statement Blocking
Multiple statements separated by semicolons are strictly forbidden to prevent SQL injection or escape attacks.

### 3. Result Clamping & Truncation
All queries without a `LIMIT` clause are automatically appended with `LIMIT 10000`. Queries requesting larger limits are clamped to the system maximum, and `truncated=True` is flagged in the response.
