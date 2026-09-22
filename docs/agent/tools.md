# Agent Tool Registry & Specification

The `packages/agent/tool_registry` provides the strict, bounded execution boundary through which the LangGraph agent interrogates datasets. The agent is never granted raw DataFrame access or arbitrary file system access.

## Registered Tools

| Tool Name | Input Arguments | Description | Output Structure |
|---|---|---|---|
| `inspect_schema` | None | Column names and dtypes | `List[ColumnSchema]` |
| `get_column_metadata` | `column: str` | Cardinality, null count, data type | `ColumnMetadata` |
| `get_unique_values` | `column: str, limit: int = 50` | Distinct non-null values (capped at 100) | `UniqueValuesResult` |
| `get_sample_rows` | `n: int = 10` | Sample records (capped at 50) | `SampleRowsResult` |
| `describe_column` | `column: str` | Mean, median, std, min, max, skewness, nulls | `ColumnStats` |
| `calculate_distribution` | `column: str` | Alias for describe_column | `ColumnStats` |
| `calculate_missingness` | None | Missing values count & pct per column | `Dict[str, MissingnessStats]` |
| `calculate_correlation` | `limit: int = 10` | Top Pearson \|r\| correlation pairs | `List[CorrelationPair]` |
| `detect_outliers` | `column: str` | IQR-based outlier bounds and count | `OutlierResult` |
| `filter_dataset` | `column, operator, value, limit` | Row match count, % and sampled records | `FilterResult` |
| `group_by` | `group_column, agg_column, agg_fn, limit` | Aggregated metrics per category | `GroupByResult` |
| `aggregate` | `column: str, agg_fn: str` | Scalar metric (mean, sum, count, etc.) | `AggregateResult` |
| `compare_segments` | `segment_column, metric_column` | Comprehensive stats across sub-populations | `SegmentComparisonResult` |
| `find_trends` | `time_column, metric_column` | Temporal slope, rate of change, direction | `TrendResult` |
| `find_anomalies` | `column, method, threshold, limit` | Z-score or IQR statistical anomalies | `AnomalyResult` |
| `test_hypothesis` | `hypothesis_type, columns, alpha` | P-values from t-test, correlation, or chi2 | `HypothesisTestResult` |
| `run_sql` | `sql: str, max_rows: int = 100` | Read-only SQL via DuckDB (capped <= 10,000) | `QueryResult` |
| `explain_sql` | `sql: str` | Execution plan from DuckDB | `str` |
