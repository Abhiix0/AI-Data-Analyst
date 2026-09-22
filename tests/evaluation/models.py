"""Data models for evaluation benchmark test cases and scoring."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    dataset_type: str = "sales"
    question: str
    expected_tools: List[str] = Field(default_factory=list)
    expected_metrics: List[str] = Field(default_factory=list)
    expected_keywords: List[str] = Field(default_factory=list)


class EvalResult(BaseModel):
    case_id: str
    passed: bool
    tool_selected: Optional[str] = None
    tool_matched: bool = False
    evidence_count: int = 0
    validation_passed: bool = False
    synthesized_findings_count: int = 0
    latency_s: float = 0.0
    error: Optional[str] = None


class BenchmarkSummary(BaseModel):
    total_cases: int
    passed_cases: int
    pass_rate: float
    tool_precision: float
    evidence_pass_rate: float
    avg_latency_s: float
    results: List[EvalResult]
