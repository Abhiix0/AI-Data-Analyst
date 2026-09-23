"""FastAPI router for analytical runs, interactive agent execution, and chat conversations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import (
    AnalysisRun,
    Dataset,
    DatasetVersion,
    Finding as DBFinding,
    ConversationTurn,
)
from apps.api.app.services.run_resolution import resolve_or_create_run, parse_uuid, resolve_parquet_path
from packages.agent.graph import run_analytical_agent
from packages.shared.storage import get_storage_client

runs_router = APIRouter(prefix="/runs", tags=["Runs & Agent"])


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language analytical question to ask about the dataset")


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="Conversational message / follow-up query")


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


class ChatTurnResponse(BaseModel):
    id: str
    run_id: str
    turn_index: int
    user_message: str
    assistant_message: str
    findings: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    created_at: datetime


@runs_router.post("/{run_id}/ask", response_model=AskQuestionResponse)
def ask_question_on_run(
    run_id: str,
    req: AskQuestionRequest,
    db: Session = Depends(get_db),
):
    """Execute LangGraph analytical agent with hard evidence verification over a run's dataset."""
    run = resolve_or_create_run(db, run_id)
    version = db.query(DatasetVersion).filter(DatasetVersion.id == run.dataset_version_id).first()
    if not version or not version.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset storage path not found for this run.",
        )
    parquet_path = resolve_parquet_path(version.storage_path)

    # Execute LangGraph agent
    state = run_analytical_agent(
        question=req.question,
        parquet_path=parquet_path,
        dataset_id=str(run.id),
    )

    # Save findings into DB
    for finding in state.synthesized_findings:
        db_finding = DBFinding(
            id=finding.id if isinstance(finding.id, uuid.UUID) else uuid.UUID(str(finding.id)),
            run_id=run.id,
            claim=finding.claim or finding.title or "Finding",
            evidence_json=[e.model_dump(mode="json") for e in state.evidence_ledger if str(e.id) in finding.evidence_ids] or ([state.evidence_ledger[0].model_dump(mode="json")] if state.evidence_ledger else []),
            evidence_strength=finding.evidence_strength or "strong",
            source_columns=finding.source_columns or [],
        )
        db.add(db_finding)
    db.commit()

    return AskQuestionResponse(
        run_id=str(run.id),
        question=req.question,
        answer=state.final_response,
        validation_passed=state.validation_passed,
        findings=[
            FindingResponse(
                id=str(f.id),
                title=f.title or f.claim or "Finding",
                description=f.description or f.claim or "",
                category=f.category,
                strength=f.strength,
                evidence_ids=f.evidence_ids,
            )
            for f in state.synthesized_findings
        ],
        evidence=[
            EvidenceResponse(
                id=str(e.id),
                metric_name=e.metric_name,
                value=e.value,
                source_query=e.source_query,
                confidence_score=e.confidence_score,
            )
            for e in state.evidence_ledger
        ],
    )


@runs_router.post("/{run_id}/chat", response_model=ChatTurnResponse)
def send_chat_message_to_run(
    run_id: str,
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
):
    """Conversational endpoint executing multi-turn grounded agent analysis."""
    run = resolve_or_create_run(db, run_id)

    version = db.query(DatasetVersion).filter(DatasetVersion.id == run.dataset_version_id).first()
    if not version or not version.storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset storage path not found for this run.",
        )
    parquet_path = resolve_parquet_path(version.storage_path)

    # Fetch prior turns for context
    past_turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.run_id == run.id)
        .order_by(ConversationTurn.turn_index.asc())
        .all()
    )

    conv_history = []
    for t in past_turns:
        conv_history.append({"role": "user", "content": t.user_message})
        conv_history.append({"role": "assistant", "content": t.assistant_message})

    # Execute Agent with conversation history
    state = run_analytical_agent(
        question=req.message,
        parquet_path=parquet_path,
        dataset_id=str(run.id),
        conversation_history=conv_history,
    )

    findings_payload = [
        {
            "id": str(f.id),
            "title": f.title or f.claim,
            "description": f.description or f.claim,
            "category": f.category,
            "strength": f.strength,
            "evidence_ids": f.evidence_ids,
        }
        for f in state.synthesized_findings
    ]

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

    # Save turn
    new_turn = ConversationTurn(
        id=uuid.uuid4(),
        run_id=run.id,
        turn_index=len(past_turns),
        user_message=req.message,
        assistant_message=state.final_response,
        findings_json=findings_payload,
        evidence_json=evidence_payload,
    )
    db.add(new_turn)

    # Save any new findings into DB findings table
    for finding in state.synthesized_findings:
        db_finding = DBFinding(
            id=finding.id if isinstance(finding.id, uuid.UUID) else uuid.UUID(str(finding.id)),
            run_id=run.id,
            claim=finding.claim or finding.title or "Finding",
            evidence_json=[e.model_dump(mode="json") for e in state.evidence_ledger if str(e.id) in finding.evidence_ids] or ([state.evidence_ledger[0].model_dump(mode="json")] if state.evidence_ledger else []),
            evidence_strength=finding.evidence_strength or "strong",
            source_columns=finding.source_columns or [],
        )
        db.add(db_finding)

    db.commit()
    db.refresh(new_turn)

    return ChatTurnResponse(
        id=str(new_turn.id),
        run_id=str(new_turn.run_id),
        turn_index=new_turn.turn_index,
        user_message=new_turn.user_message,
        assistant_message=new_turn.assistant_message,
        findings=new_turn.findings_json,
        evidence=new_turn.evidence_json,
        created_at=new_turn.created_at,
    )


@runs_router.get("/{run_id}/chat/history", response_model=List[ChatTurnResponse])
def get_chat_history(
    run_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full chronological conversation history for an analysis run."""
    try:
        run = resolve_or_create_run(db, run_id)
        run_uid = run.id
    except HTTPException:
        return []

    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.run_id == run_uid)
        .order_by(ConversationTurn.turn_index.asc())
        .all()
    )
    return [
        ChatTurnResponse(
            id=str(t.id),
            run_id=str(t.run_id),
            turn_index=t.turn_index,
            user_message=t.user_message,
            assistant_message=t.assistant_message,
            findings=t.findings_json,
            evidence=t.evidence_json,
            created_at=t.created_at,
        )
        for t in turns
    ]


class RunFindingItemResponse(BaseModel):
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


@runs_router.get("/{run_id}/findings", response_model=List[RunFindingItemResponse])
def get_run_findings(
    run_id: str,
    is_pinned: Optional[bool] = None,
    strength: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all findings for a given analysis run with optional filtering."""
    try:
        run = resolve_or_create_run(db, run_id)
        run_uid = run.id
    except HTTPException:
        return []

    query = db.query(DBFinding).filter(DBFinding.run_id == run_uid)
    if is_pinned is not None:
        query = query.filter(DBFinding.is_pinned == is_pinned)
    if strength:
        query = query.filter(DBFinding.evidence_strength == strength)

    findings = query.order_by(DBFinding.created_at.desc()).all()
    return [
        RunFindingItemResponse(
            id=str(f.id),
            run_id=str(f.run_id),
            claim=f.claim,
            evidence_json=f.evidence_json or [],
            evidence_strength=f.evidence_strength,
            source_columns=f.source_columns or [],
            query=f.query,
            is_pinned=f.is_pinned,
            user_notes=f.user_notes,
            parent_finding_id=str(f.parent_finding_id) if f.parent_finding_id else None,
            created_at=f.created_at,
        )
        for f in findings
    ]


class RunInvestigationItemResponse(BaseModel):
    id: str
    run_id: str
    parent_finding_id: Optional[str] = None
    query: str
    status: str
    findings_count: int
    summary: Optional[str] = None
    created_at: datetime


@runs_router.get("/{run_id}/investigations", response_model=List[RunInvestigationItemResponse])
def get_run_investigations(
    run_id: str,
    db: Session = Depends(get_db),
):
    """List all drill-down investigations performed on a run."""
    from apps.api.app.models import Investigation

    try:
        run = resolve_or_create_run(db, run_id)
        run_uid = run.id
    except HTTPException:
        return []

    investigations = (
        db.query(Investigation)
        .filter(Investigation.run_id == run_uid)
        .order_by(Investigation.created_at.desc())
        .all()
    )
    return [
        RunInvestigationItemResponse(
            id=str(inv.id),
            run_id=str(inv.run_id),
            parent_finding_id=str(inv.parent_finding_id) if inv.parent_finding_id else None,
            query=inv.query,
            status=inv.status,
            findings_count=inv.findings_count,
            summary=inv.summary,
            created_at=inv.created_at,
        )
        for inv in investigations
    ]

