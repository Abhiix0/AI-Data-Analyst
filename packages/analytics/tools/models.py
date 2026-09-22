"""Pydantic models for analytics tool outputs."""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class DatasetShape(BaseModel):
    rows: int
    columns: int


class ColumnSchema(BaseModel):
    name: str
    dtype: str


class ColumnMetadata(BaseModel):
    column: str
    dtype: str
    null_count: int
    unique_count: int


class ColumnStats(BaseModel):
    column: str
    mean: float
    median: float
    std: float
    min: float
    max: float
    skew: float
    null_count: int


class MissingnessStats(BaseModel):
    column: str
    count: int
    pct: float


class CorrelationPair(BaseModel):
    col_a: str
    col_b: str
    r: float
    direction: Literal["positive", "negative"]


class OutlierResult(BaseModel):
    column: str
    count: int
    pct: float
    lower_bound: float
    upper_bound: float


class CategoricalStats(BaseModel):
    column: str
    unique_count: int
    top_values: Dict[str, int]
    null_count: int


class DatetimeStats(BaseModel):
    column: str
    min: str
    max: str
    range_days: int
    null_count: int
    null_pct: float
    unique_dates: int
    is_time_series: bool


class DuplicateStats(BaseModel):
    duplicate_rows: int
    pct: float


class SampleRowsResult(BaseModel):
    total_rows: int
    sample_count: int
    records: List[Dict[str, Any]]


class UniqueValuesResult(BaseModel):
    column: str
    total_unique: int
    values: List[Any]


class FilterResult(BaseModel):
    column: str
    operator: str
    value: Any
    total_rows: int
    matched_rows: int
    matched_pct: float
    sampled_records: List[Dict[str, Any]]


class GroupByResult(BaseModel):
    group_column: str
    agg_column: str
    agg_fn: str
    groups: List[Dict[str, Any]]


class AggregateResult(BaseModel):
    column: str
    agg_fn: str
    value: Optional[float]


class SegmentComparisonResult(BaseModel):
    segment_column: str
    metric_column: str
    segments: Dict[str, Dict[str, float]]


class TrendResult(BaseModel):
    time_column: str
    metric_column: str
    direction: Literal["increasing", "decreasing", "stable"]
    slope: float
    start_value: float
    end_value: float
    pct_change: float


class AnomalyResult(BaseModel):
    column: str
    method: str
    anomaly_count: int
    anomaly_pct: float
    sample_anomalies: List[Dict[str, Any]]


class HypothesisTestResult(BaseModel):
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    alpha: float
    interpretation: str


class ProfileResult(BaseModel):
    shape: DatasetShape
    dtypes: Dict[str, str]
    missing: Dict[str, MissingnessStats]
    duplicate_rows: int
    numeric_stats: Dict[str, ColumnStats]
    top_correlations: List[CorrelationPair]
    outliers: Dict[str, OutlierResult]
    categorical_stats: Dict[str, CategoricalStats]
    datetime_stats: Dict[str, DatetimeStats]
