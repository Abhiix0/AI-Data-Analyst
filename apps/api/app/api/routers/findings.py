"""API router for Finding drill-down investigations, saved findings, and notes."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import AnalysisRun, DatasetVersion, Finding as DBFinding, Investigation
from packages.agent.graph import run_analytical_agent

findings_router = APIRouter(prefix="/findings", tags=["Findings & Drill-downs"])


def _parse_uuid(val: Any) -> Optional[uuid.UUID]:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


class UpdateFindingRequest(BaseModel):
    is_pinned: Optional[bool] = Field(None, description="Whether to pin/bookmark this finding")
    user_notes: Optional[str] = Field(None, description="User reflections, notes, or hypothesis")


class FindingDetailResponse(BaseModel):
    id: str
    run_id: str
    claim: str
    evidence_json: List[Dict[str, Any]]
    evidence_strength: str
    source_columns: List[str]
    query: Optional[str] = None
    is_pinned: bool
    user_notes: Optional[str] = None
    parent_finding_id: Optional[str] = None
    created_at: datetime
    investigations_count: int = 0


class InvestigateFindingResponse(BaseModel):
    investigation_id: str
    parent_finding_id: str
    parent_claim: str
    investigation_query: str
    answer: str
    validation_passed: bool
    new_findings: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]


@findings_router.get("/{finding_id}", response_model=FindingDetailResponse)
def get_finding(
    finding_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed information and evidence for a specific finding."""
    fid = _parse_uuid(finding_id)
    finding = db.query(DBFinding).filter(DBFinding.id == fid).first() if fid else None
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID '{finding_id}' not found.",
        )

    inv_count = db.query(Investigation).filter(Investigation.parent_finding_id == finding.id).count()

    return FindingDetailResponse(
        id=str(finding.id),
        run_id=str(finding.run_id),
        claim=finding.claim,
        evidence_json=finding.evidence_json or [],
        evidence_strength=finding.evidence_strength,
        source_columns=finding.source_columns or [],
        query=finding.query,
        is_pinned=finding.is_pinned,
        user_notes=finding.user_notes,
        parent_finding_id=str(finding.parent_finding_id) if finding.parent_finding_id else None,
        created_at=finding.created_at,
        investigations_count=inv_count,
    )


@findings_router.patch("/{finding_id}", response_model=FindingDetailResponse)
def update_finding(
    finding_id: str,
    req: UpdateFindingRequest,
    db: Session = Depends(get_db),
):
    """Update bookmark/pinned status and user notes for a finding."""
    fid = _parse_uuid(finding_id)
    finding = db.query(DBFinding).filter(DBFinding.id == fid).first() if fid else None
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID '{finding_id}' not found.",
        )

    if req.is_pinned is not None:
        finding.is_pinned = req.is_pinned
    if req.user_notes is not None:
        finding.user_notes = req.user_notes

    db.commit()
    db.refresh(finding)

    inv_count = db.query(Investigation).filter(Investigation.parent_finding_id == finding.id).count()

    return FindingDetailResponse(
        id=str(finding.id),
        run_id=str(finding.run_id),
        claim=finding.claim,
        evidence_json=finding.evidence_json or [],
        evidence_strength=finding.evidence_strength,
        source_columns=finding.source_columns or [],
        query=finding.query,
        is_pinned=finding.is_pinned,
        user_notes=finding.user_notes,
        parent_finding_id=str(finding.parent_finding_id) if finding.parent_finding_id else None,
        created_at=finding.created_at,
        investigations_count=inv_count,
    )


@findings_router.post("/{finding_id}/investigate", response_model=InvestigateFindingResponse)
def investigate_finding(
    finding_id: str,
    db: Session = Depends(get_db),
):
    """Trigger a focused drill-down investigation exploring drivers and causes behind a specific finding."""
    fid = _parse_uuid(finding_id)
    finding = db.query(DBFinding).filter(DBFinding.id == fid).first() if fid else None
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID '{finding_id}' not found.",
        )

    run = db.query(AnalysisRun).filter(AnalysisRun.id == finding.run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated AnalysisRun not found.",
        )

    version = db.query(DatasetVersion).filter(DatasetVersion.id == run.dataset_version_id).first()
    if not version or not version.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset storage path not found for this finding.",
        )

    # Construct targeted drill-down question
    cols_str = ", ".join(finding.source_columns) if finding.source_columns else "related variables"
    investigation_query = (
        f"Investigate the underlying drivers and deeper patterns behind this finding: '{finding.claim}'. "
        f"Focus on relationships with {cols_str} and segment differences."
    )

    # Execute LangGraph analytical agent
    state = run_analytical_agent(
        question=investigation_query,
        parquet_path=version.storage_path,
        dataset_id=str(run.id),
    )

    # Save child findings into DB with parent link
    new_findings_payload = []
    child_ids = []
    for f in state.synthesized_findings:
        child_id = uuid.uuid4()
        child_ids.append(str(child_id))
        db_child = DBFinding(
            id=child_id,
            run_id=run.id,
            claim=f.claim or f.title or "Child Finding",
            evidence_json=[e.model_dump(mode="json") for e in state.evidence_ledger if str(e.id) in f.evidence_ids] or ([state.evidence_ledger[0].model_dump(mode="json")] if state.evidence_ledger else []),
            evidence_strength=f.evidence_strength or "strong",
            source_columns=f.source_columns or finding.source_columns or [],
            parent_finding_id=finding.id,
        )
        db.add(db_child)
        new_findings_payload.append({
            "id": str(child_id),
            "title": f.title or f.claim,
            "description": f.description or f.claim,
            "category": f.category,
            "strength": f.strength,
            "evidence_ids": f.evidence_ids,
        })

    # Save Investigation record
    investigation_id = uuid.uuid4()
    investigation = Investigation(
        id=investigation_id,
        run_id=run.id,
        parent_finding_id=finding.id,
        query=investigation_query,
        status="completed",
        findings_count=len(new_findings_payload),
        summary=state.final_response,
        result_json={
            "validation_passed": state.validation_passed,
            "child_finding_ids": child_ids,
            "evidence_count": len(state.evidence_ledger),
        },
    )
    db.add(investigation)
    db.commit()

    evidence_payload = [
        {
            "id": str(e.id),
            "metric_name": e.metric_name,
            "value": e.value,
            "source_query": e.source_query,
            "confidence_score": e.confidence_score,
        }
        for e in state.evidence_ledger
    ]

    return InvestigateFindingResponse(
        investigation_id=str(investigation_id),
        parent_finding_id=str(finding.id),
        parent_claim=finding.claim,
        investigation_query=investigation_query,
        answer=state.final_response,
        validation_passed=state.validation_passed,
        new_findings=new_findings_payload,
        evidence=evidence_payload,
    )
