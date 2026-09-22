"""Agent tool registry mapping tool names to schemas, descriptions, and callables."""
from __future__ import annotations
import inspect
from typing import Any, Callable, Dict, List, Optional, Type
import polars as pl
from pydantic import BaseModel, Field, ConfigDict

from packages.evidence.models import Evidence
from packages.analytics.tools.schema import inspect_schema
from packages.analytics.tools.metadata import (
    get_column_metadata,
    get_unique_values,
    get_sample_rows,
)
from packages.analytics.tools.distribution import describe_column
from packages.analytics.tools.missingness import calculate_missingness
from packages.analytics.tools.correlation import calculate_correlation
from packages.analytics.tools.outliers import detect_outliers
from packages.analytics.tools.filtering import filter_dataset
from packages.analytics.tools.grouping import group_by, aggregate
from packages.analytics.tools.segments import compare_segments
from packages.analytics.tools.trends import find_trends
from packages.analytics.tools.anomalies import find_anomalies
from packages.analytics.tools.hypothesis import test_hypothesis
from packages.analytics.tools.sql import run_sql, explain_sql


# ── Pydantic Input Schemas for LLM Tool Calling ─────────────────────

class InspectSchemaInput(BaseModel):
    pass

class GetColumnMetadataInput(BaseModel):
    column: str = Field(..., description="Target column name to inspect")

class GetUniqueValuesInput(BaseModel):
    column: str = Field(..., description="Target categorical column")
    limit: int = Field(50, description="Max distinct values to return (capped at 100)")

class GetSampleRowsInput(BaseModel):
    n: int = Field(10, description="Number of sample records to return (capped at 50)")

class DescribeColumnInput(BaseModel):
    column: str = Field(..., description="Numeric column name to calculate summary statistics")

class CalculateMissingnessInput(BaseModel):
    pass

class CalculateCorrelationInput(BaseModel):
    limit: int = Field(10, description="Number of top correlation pairs to return")

class DetectOutliersInput(BaseModel):
    column: str = Field(..., description="Numeric column to run IQR outlier detection on")

class FilterDatasetInput(BaseModel):
    column: str = Field(..., description="Column to filter by")
    operator: str = Field(..., description="Comparison operator: ==, !=, >, >=, <, <=, contains")
    value: Any = Field(..., description="Filter threshold or matching string")
    limit: int = Field(20, description="Max matching sample records to return (capped at 50)")

class GroupByInput(BaseModel):
    group_column: str = Field(..., description="Categorical column to group by")
    agg_column: str = Field(..., description="Numeric column to aggregate")
    agg_fn: str = Field("mean", description="Aggregation function: mean, sum, count, min, max, median, std")
    limit: int = Field(20, description="Max top grouped items to return")

class AggregateInput(BaseModel):
    column: str = Field(..., description="Numeric column to compute scalar aggregate on")
    agg_fn: str = Field("mean", description="Aggregation function: mean, sum, count, min, max, median, std")

class CompareSegmentsInput(BaseModel):
    segment_column: str = Field(..., description="Categorical segment column (e.g. churn, gender, tier)")
    metric_column: str = Field(..., description="Numeric metric column to compare across segments")

class FindTrendsInput(BaseModel):
    time_column: str = Field(..., description="Date or chronological order column")
    metric_column: str = Field(..., description="Numeric metric column to evaluate trend direction")

class FindAnomaliesInput(BaseModel):
    column: str = Field(..., description="Numeric column to inspect for statistical anomalies")
    method: str = Field("zscore", description="Detection method: 'zscore' or 'iqr'")
    threshold: float = Field(3.0, description="Z-score cutoff standard deviations (default 3.0)")
    limit: int = Field(10, description="Max sampled anomaly records to return")

class TestHypothesisInput(BaseModel):
    hypothesis_type: str = Field(..., description="Statistical test: 'correlation', 'two_sample_ttest', or 'chi_square'")
    columns: List[str] = Field(..., description="Columns required for the statistical test")
    alpha: float = Field(0.05, description="Significance level threshold (default 0.05)")

class RunSqlInput(BaseModel):
    sql: str = Field(..., description="Read-only SELECT or WITH (CTE) SQL query string")
    max_rows: int = Field(100, description="Max rows to return (capped at 10,000)")

class ExplainSqlInput(BaseModel):
    sql: str = Field(..., description="SQL query string to explain")


# ── Registry Definition ─────────────────────────────────────────────

class ToolDefinition(BaseModel):
    """Encapsulation of a registered tool definition."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    input_schema: Type[BaseModel]
    description: str


class ToolRegistry:
    """Registry maintaining all available tools for agent invocation."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        input_schema: Type[BaseModel],
        executor: Callable,
        description: str,
    ) -> None:
        """Register a new tool."""
        self._tools[name] = ToolDefinition(
            name=name,
            input_schema=input_schema,
            description=description,
        )
        self._executors[name] = executor

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def execute(self, name: str, df: Optional[pl.DataFrame] = None, parquet_path: Optional[str] = None, **kwargs) -> Any:
        """Execute a registered tool by name with arguments and wrap results in Evidence."""
        if name not in self._executors:
            raise ValueError(f"Tool '{name}' is not registered in ToolRegistry.")
        executor = self._executors[name]

        # Pass appropriate source (df or parquet_path)
        sig = inspect.signature(executor)
        if "df" in sig.parameters and df is not None:
            return executor(df=df, **kwargs)
        elif "parquet_path" in sig.parameters and parquet_path is not None:
            return executor(parquet_path=parquet_path, **kwargs)
        else:
            return executor(**kwargs)


# ── Default Tool Registry Singleton ──────────────────────────────────

registry = ToolRegistry()

# 1. Schema & Metadata Tools
registry.register(
    name="inspect_schema",
    input_schema=InspectSchemaInput,
    executor=lambda df, **kw: inspect_schema(df),
    description="Inspect dataset column names, types, and structure.",
)

registry.register(
    name="get_column_metadata",
    input_schema=GetColumnMetadataInput,
    executor=lambda df, column, **kw: get_column_metadata(df, column=column),
    description="Retrieve data type, cardinality (unique count), and missingness count for a single column.",
)

registry.register(
    name="get_unique_values",
    input_schema=GetUniqueValuesInput,
    executor=lambda df, column, limit=50, **kw: get_unique_values(df, column=column, limit=limit),
    description="Retrieve distinct categorical values for a column, capped at limit.",
)

registry.register(
    name="get_sample_rows",
    input_schema=GetSampleRowsInput,
    executor=lambda df, n=10, **kw: get_sample_rows(df, n=n),
    description="Retrieve a small sample of rows from the dataset (max 50).",
)

# 2. Distribution & Profiling Tools
registry.register(
    name="describe_column",
    input_schema=DescribeColumnInput,
    executor=lambda df, column, **kw: describe_column(df, column=column),
    description="Calculate mean, median, standard deviation, min, max, skewness, and null count for a numeric column.",
)

registry.register(
    name="calculate_distribution",
    input_schema=DescribeColumnInput,
    executor=lambda df, column, **kw: describe_column(df, column=column),
    description="Alias to describe_column: calculates numeric distribution metrics.",
)

registry.register(
    name="calculate_missingness",
    input_schema=CalculateMissingnessInput,
    executor=lambda df, **kw: calculate_missingness(df),
    description="Calculate missing value counts and null percentages across all columns.",
)

registry.register(
    name="calculate_correlation",
    input_schema=CalculateCorrelationInput,
    executor=lambda df, limit=10, **kw: calculate_correlation(df, limit=limit),
    description="Calculate top pairwise Pearson correlation coefficients (|r|) between numeric columns.",
)

registry.register(
    name="detect_outliers",
    input_schema=DetectOutliersInput,
    executor=lambda df, column, **kw: detect_outliers(df, column=column),
    description="Detect numeric anomalies and calculate percentage outside IQR bounds [Q1 - 1.5*IQR, Q3 + 1.5*IQR].",
)

# 3. Filtering, Grouping & Segmentation Tools
registry.register(
    name="filter_dataset",
    input_schema=FilterDatasetInput,
    executor=lambda df, column, operator, value, limit=20, **kw: filter_dataset(df, column=column, operator=operator, value=value, limit=limit),
    description="Filter rows by a condition (==, !=, >, >=, <, <=, contains) and return match count, percentage, and sample records.",
)

registry.register(
    name="group_by",
    input_schema=GroupByInput,
    executor=lambda df, group_column, agg_column, agg_fn="mean", limit=20, **kw: group_by(df, group_column=group_column, agg_column=agg_column, agg_fn=agg_fn, limit=limit),
    description="Group by a categorical column and aggregate a numeric column (mean, sum, count, min, max, median, std).",
)

registry.register(
    name="aggregate",
    input_schema=AggregateInput,
    executor=lambda df, column, agg_fn="mean", **kw: aggregate(df, column=column, agg_fn=agg_fn),
    description="Compute a single scalar aggregate metric over a numeric column.",
)

registry.register(
    name="compare_segments",
    input_schema=CompareSegmentsInput,
    executor=lambda df, segment_column, metric_column, **kw: compare_segments(df, segment_column=segment_column, metric_column=metric_column),
    description="Compare distribution metrics (mean, median, std, min, max, count) across categorical segments.",
)

registry.register(
    name="find_trends",
    input_schema=FindTrendsInput,
    executor=lambda df, time_column, metric_column, **kw: find_trends(df, time_column=time_column, metric_column=metric_column),
    description="Analyze temporal direction, rate of change, and slope for a metric column across time.",
)

registry.register(
    name="find_anomalies",
    input_schema=FindAnomaliesInput,
    executor=lambda df, column, method="zscore", threshold=3.0, limit=10, **kw: find_anomalies(df, column=column, method=method, threshold=threshold, limit=limit),
    description="Find statistical anomalies using Z-score (> 3 std dev) or IQR methods.",
)

registry.register(
    name="test_hypothesis",
    input_schema=TestHypothesisInput,
    executor=lambda df, hypothesis_type, columns, alpha=0.05, **kw: test_hypothesis(df, hypothesis_type=hypothesis_type, columns=columns, alpha=alpha),
    description="Run a rigorous statistical test: Pearson correlation p-value, Welch's two-sample t-test, or Chi-Square independence.",
)

# 4. SQL Engine Tools
registry.register(
    name="run_sql",
    input_schema=RunSqlInput,
    executor=lambda parquet_path, sql, max_rows=100, **kw: run_sql(parquet_path=parquet_path, sql=sql, max_rows=max_rows),
    description="Execute an arbitrary read-only analytical SQL query (SELECT / WITH) over the dataset via DuckDB.",
)

registry.register(
    name="explain_sql",
    input_schema=ExplainSqlInput,
    executor=lambda parquet_path, sql, **kw: explain_sql(parquet_path=parquet_path, sql=sql),
    description="Explain the DuckDB physical execution plan for a SQL query.",
)
