"""Shared analysis context — passed through the entire pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class AnalysisContext:
    # Input
    df: pd.DataFrame
    file_name: str

    # Agent outputs (populated as pipeline runs)
    profile: Dict[str, Any] = field(default_factory=dict)
    chart_paths: List[Any] = field(default_factory=list)  # List of chart metadata dicts
    patterns: Dict[str, Any] = field(default_factory=dict)
    outliers: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    report_path: Optional[str] = None

    # Status tracking
    errors: List[str] = field(default_factory=list)

    def has_numeric_columns(self) -> bool:
        return len(self.df.select_dtypes(include="number").columns) > 0

    def has_categorical_columns(self) -> bool:
        return len(self.df.select_dtypes(include=["object", "category"]).columns) > 0

    def shape_summary(self) -> str:
        r, c = self.df.shape
        return f"{r:,} rows x {c} columns"
