"""Typed Evidence and Finding domain models."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """An atomic, verified piece of statistical evidence backing an analytical claim."""
    metric_name: str = Field(..., description="e.g. pearson_correlation, outlier_pct, missing_pct, mean")
    value: Union[float, int, str, dict, list] = Field(..., description="Computed metric value")
    source_tool: str = Field(..., description="Tool or function that produced this number")
    source_columns: List[str] = Field(default_factory=list, description="Columns involved in the calculation")
    computed_at: datetime = Field(default_factory=utc_now)


class Finding(BaseModel):
    """An analytical insight backed by verified statistical evidence.

    Enforces that at least one Evidence item must be attached.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    claim: str = Field(..., description="Plain-English assertion synthesized from evidence")
    evidence: List[Evidence] = Field(..., min_length=1, description="List of verified Evidence objects")
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] = Field(
        ...,
        description="Deterministic strength classification based on sample size and effect size",
    )
    dataset_version_id: uuid.UUID = Field(..., description="Target dataset version UUID")
    analysis_run_id: Optional[uuid.UUID] = Field(None, description="Associated analysis run UUID")
    source_columns: List[str] = Field(default_factory=list, description="Primary columns involved")
    query: Optional[str] = Field(None, description="SQL query or tool call expression")
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("evidence")
    @classmethod
    def validate_non_empty_evidence(cls, v: List[Evidence]) -> List[Evidence]:
        if not v:
            raise ValueError("A Finding cannot be constructed without at least one Evidence item.")
        return v
