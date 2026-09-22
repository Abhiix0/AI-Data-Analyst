"""FastAPI router for analytical runs and interactive agent execution."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.models.dataset import AnalysisRun, Dataset, DatasetVersion, Finding as DBFinding
from packages.agent.graph import run_analytical_agent
from packages.shared.storage import get_storage_client

runs_router = APIRouter(prefix="/runs", tags=["Runs & Agent"])


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language analytical question to ask about the dataset")


class FindingResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    strength: str
    evidence_ids: List[str]


class EvidenceResponse(BaseModel):
    id: str
    metric_name: str
    value: Any
    source_query: Optional[str] = None
    confidence_score: float


class AskQuestionResponse(BaseModel):
    run_id: str
    question: str
    answer: str
    validation_passed: bool
    findings: List[FindingResponse]
    evidence: List[EvidenceResponse]


@runs_router.post("/{run_id}/ask", response_model=AskQuestionResponse)
def ask_question_on_run(
    run_id: str,
    req: AskQuestionRequest,
    db: Session = Depends(get_db),
):
    """Execute LangGraph analytical agent with hard evidence verification over a run's dataset."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    
    parquet_path = None
    if run:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == run.dataset_version_id).first()
        if version:
            parquet_path = version.storage_path

    # If run_id is actually a dataset_id
    if not parquet_path:
        dataset = db.query(Dataset).filter(Dataset.id == run_id).first()
        if dataset:
            version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset.id).order_by(DatasetVersion.version_num.desc()).first()
            if version:
                parquet_path = version.storage_path
                # Create run record if missing
                if not run:
                    run = AnalysisRun(
                        id=str(uuid.uuid4()),
                        dataset_version_id=version.id,
                        status="COMPLETED",
                        profile_json={},
                    )
                    db.add(run)
                    db.commit()

    if not parquet_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run or Dataset with ID '{run_id}' not found.",
        )

    # Execute LangGraph agent
    state = run_analytical_agent(
        question=req.question,
        parquet_path=parquet_path,
        dataset_id=run.id if run else None,
    )

    # Save findings into DB
    for finding in state.synthesized_findings:
        db_finding = DBFinding(
            id=finding.id,
            run_id=run.id if run else run_id,
            title=finding.title,
            description=finding.description,
            category=finding.category,
            strength=finding.strength,
            evidence_json=[e.model_dump() for e in state.evidence_ledger if e.id in finding.evidence_ids] or [state.evidence_ledger[0].model_dump()] if state.evidence_ledger else [],
        )
        db.add(db_finding)
    db.commit()

    return AskQuestionResponse(
        run_id=run.id if run else run_id,
        question=req.question,
        answer=state.final_response,
        validation_passed=state.validation_passed,
        findings=[
            FindingResponse(
                id=f.id,
                title=f.title,
                description=f.description,
                category=f.category,
                strength=f.strength,
                evidence_ids=f.evidence_ids,
            )
            for f in state.synthesized_findings
        ],
        evidence=[
            EvidenceResponse(
                id=e.id,
                metric_name=e.metric_name,
                value=e.value,
                source_query=e.source_query,
                confidence_score=e.confidence_score,
            )
            for e in state.evidence_ledger
        ],
    )
