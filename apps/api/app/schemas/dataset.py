"""Pydantic schemas for dataset API requests and responses."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KaggleDatasetRequest(BaseModel):
    """Request payload for Kaggle dataset ingestion."""
    dataset_ref: str = Field(..., description="Kaggle reference in 'owner/dataset-name' format")
    dataset_name: Optional[str] = Field(None, description="Optional custom name for the dataset")


class DatasetVersionResponse(BaseModel):
    """Response payload for a dataset version."""
    id: uuid.UUID
    dataset_id: uuid.UUID
    storage_path: str
    row_count: int
    col_count: int
    schema_json: Dict[str, Any]
    created_at: datetime


class DatasetResponse(BaseModel):
    """Response payload for a dataset entity."""
    id: uuid.UUID
    name: str
    created_at: datetime
    latest_version: Optional[DatasetVersionResponse] = None
