"""API router for investigations and deep dive history."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import Investigation

investigations_router = APIRouter(prefix="/investigations", tags=["Investigations"])


def _parse_uuid(val: Any) -> Optional[uuid.UUID]:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


class InvestigationDetailResponse(BaseModel):
    id: str
    run_id: str
    parent_finding_id: Optional[str] = None
    query: str
    status: str
    findings_count: int
    summary: Optional[str] = None
    result_json: Dict[str, Any]
    created_at: datetime


@investigations_router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
def get_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific drill-down investigation."""
    inv_id = _parse_uuid(investigation_id)
    inv = db.query(Investigation).filter(Investigation.id == inv_id).first() if inv_id else None
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found.",
        )

    return InvestigationDetailResponse(
        id=str(inv.id),
        run_id=str(inv.run_id),
        parent_finding_id=str(inv.parent_finding_id) if inv.parent_finding_id else None,
        query=inv.query,
        status=inv.status,
        findings_count=inv.findings_count,
        summary=inv.summary,
        result_json=inv.result_json or {},
        created_at=inv.created_at,
    )
