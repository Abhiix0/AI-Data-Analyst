# Deterministic Analytics Tool Functions

The `packages/analytics/tools` module provides pure, deterministic analytics functions over Polars DataFrames. Every function has typed Pydantic input and output schemas.

## Tool Registry

| Tool | Signature | Output Model | Description & Thresholds |
|---|---|---|---|
| `inspect_schema` | `(df: pl.DataFrame)` | `List[ColumnSchema]` | Returns column names and data types. |
| `describe_column` | `(df: pl.DataFrame, column: str)` | `Optional[ColumnStats]` | Calculates mean, median, std, min, max, skewness, and null count. All rounded to 4 decimals. |
| `calculate_missingness` | `(df: pl.DataFrame)` | `Dict[str, MissingnessStats]` | Computes null count and percentage for columns with missing values. |
| `calculate_correlation` | `(df: pl.DataFrame, limit=10)` | `List[CorrelationPair]` | Top correlation pairs sorted by absolute Pearson \|r\|. Direction: `positive` or `negative`. |
| `detect_outliers` | `(df: pl.DataFrame, column: str)` | `Optional[OutlierResult]` | Interquartile Range (IQR) outlier detection with bounds [Q1 - 1.5×IQR, Q3 + 1.5×IQR]. Minimum 10 non-null values threshold. |
| `describe_categorical` | `(df: pl.DataFrame, column: str)` | `Optional[CategoricalStats]` | Computes unique count, null count, and top-5 value frequencies. |
| `infer_datetime_columns` | `(df: pl.DataFrame)` | `Dict[str, DatetimeStats]` | Identifies datetime columns via sample parsing (>=80% success). Evaluates time-series heuristic (null_pct < 10% and unique_dates > 50% of rows). |
| `count_duplicate_rows` | `(df: pl.DataFrame)` | `DuplicateStats` | Computes duplicate row count and duplicate percentage. |

## Guarantees
1. **Purity**: Functions do not perform side effects or network I/O.
2. **Determinism**: Identical data always yields identical output.
3. **No Hallucinations**: Numeric calculations rely exclusively on Polars vectorized SIMD routines.
