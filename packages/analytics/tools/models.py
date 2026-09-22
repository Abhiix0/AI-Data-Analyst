"""Pydantic models for analytics tool outputs."""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class DatasetShape(BaseModel):
    rows: int
    columns: int


class ColumnSchema(BaseModel):
    name: str
    dtype: str


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
