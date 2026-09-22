"""API router for Finding drill-down investigations and deep dives."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import AnalysisRun, DatasetVersion, Finding as DBFinding
from packages.agent.graph import run_analytical_agent

findings_router = APIRouter(prefix="/findings", tags=["Findings & Drill-downs"])


def _parse_uuid(val: Any) -> Optional[uuid.UUID]:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


class InvestigateFindingResponse(BaseModel):
    parent_finding_id: str
    parent_claim: str
    investigation_query: str
    answer: str
    validation_passed: bool
    new_findings: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]


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

    # Save child findings into DB
    new_findings_payload = []
    for f in state.synthesized_findings:
        child_id = uuid.uuid4()
        db_child = DBFinding(
            id=child_id,
            run_id=run.id,
            claim=f.claim or f.title or "Child Finding",
            evidence_json=[e.model_dump(mode="json") for e in state.evidence_ledger if str(e.id) in f.evidence_ids] or [state.evidence_ledger[0].model_dump(mode="json")] if state.evidence_ledger else [],
            evidence_strength=f.evidence_strength or "strong",
            source_columns=f.source_columns or finding.source_columns or [],
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
        parent_finding_id=str(finding.id),
        parent_claim=finding.claim,
        investigation_query=investigation_query,
        answer=state.final_response,
        validation_passed=state.validation_passed,
        new_findings=new_findings_payload,
        evidence=evidence_payload,
    )
