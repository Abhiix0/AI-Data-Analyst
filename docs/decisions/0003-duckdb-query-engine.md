# ADR 0003: DuckDB Embedded Analytical SQL Engine

## Status
Accepted

## Context
While pure Polars functions handle predefined profiling statistics efficiently, the analytical agent and exploratory user queries require arbitrary SQL transformations, filtering, multi-column group-by aggregations, and window functions without risking database corruption or unbounded execution.

## Decision
We introduce DuckDB (`duckdb_engine.py` and `sql_guard.py`):
1. **Embedded & In-Memory**: DuckDB runs in-process with zero network latency, querying Parquet files directly via vectorized SIMD routines.
2. **Strict Query Guardrails**: Every query passes through `sql_guard.py` before execution. Only `SELECT` and `WITH` statements are permitted. Destructive keywords and statement-stacking are blocked.
3. **Bounded Memory**: All query executions are capped with statement row limits (`LIMIT 10000`) and execution timeouts.

## Consequences
- The agent can synthesize custom SQL queries dynamically during multi-hop investigation.
- No malicious or destructive query can affect the server, file system, or database.
- Large datasets are queried in milliseconds directly from Parquet files without full in-memory loading.
