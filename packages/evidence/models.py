"""Typed Evidence and Finding domain models."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """An atomic, verified piece of statistical evidence backing an analytical claim."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    metric_name: str = Field(..., description="e.g. pearson_correlation, outlier_pct, missing_pct, mean")
    value: Union[float, int, str, dict, list] = Field(..., description="Computed metric value")
    source_tool: str = Field(..., description="Tool or function that produced this number")
    source_columns: List[str] = Field(default_factory=list, description="Columns involved in the calculation")
    source_query: Optional[str] = Field(None, description="Exact tool invocation or query string")
    confidence_score: float = Field(1.0, description="Confidence score [0.0 - 1.0]")
    computed_at: datetime = Field(default_factory=utc_now)


class Finding(BaseModel):
    """An analytical insight backed by verified statistical evidence.

    Enforces that at least one Evidence item must be attached or referenced.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: Optional[str] = None
    claim: Optional[str] = Field(None, description="Plain-English assertion synthesized from evidence")
    description: Optional[str] = None
    category: str = "trend"
    evidence: List[Evidence] = Field(default_factory=list, description="List of verified Evidence objects")
    evidence_ids: List[str] = Field(default_factory=list, description="UUID strings of attached evidence")
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] = Field(
        "strong",
        description="Deterministic strength classification based on sample size and effect size",
    )
    dataset_version_id: Optional[uuid.UUID] = Field(None, description="Target dataset version UUID")
    analysis_run_id: Optional[uuid.UUID] = Field(None, description="Associated analysis run UUID")
    source_columns: List[str] = Field(default_factory=list, description="Primary columns involved")
    query: Optional[str] = Field(None, description="SQL query or tool call expression")
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def strength(self) -> str:
        return self.evidence_strength

    @model_validator(mode="after")
    def validate_and_populate(self) -> Finding:
        if not self.evidence and not self.evidence_ids:
            raise ValueError("A Finding cannot be constructed without at least one Evidence item.")
        if not self.claim and self.description:
            self.claim = self.description
        if not self.description and self.claim:
            self.description = self.claim
        if not self.title:
            self.title = (self.claim or "Analytical Finding")[:60]
        if self.evidence and not self.evidence_ids:
            self.evidence_ids = [str(e.id) for e in self.evidence]
        return self
