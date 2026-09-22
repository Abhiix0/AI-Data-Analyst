"""API router for generating and downloading comprehensive analysis reports."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import AnalysisRun, Dataset, DatasetVersion, Finding as DBFinding, Investigation, Report as DBReport
from packages.analytics.briefing import DatasetBriefing
from packages.analytics.reports import ReportConfig, ReportGenerator
from packages.shared.storage import get_storage_client

reports_router = APIRouter(prefix="", tags=["Reports"])


def _parse_uuid(val: Any) -> Optional[uuid.UUID]:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


class GenerateReportRequest(BaseModel):
    title: Optional[str] = Field("Automated Data Analysis Report", description="Custom title for the report")
    include_briefing: bool = True
    include_findings: bool = True
    include_pinned_only: bool = False
    include_investigations: bool = True
    include_evidence_ledger: bool = True
    include_visualizations: bool = True


class ReportItemResponse(BaseModel):
    id: str
    run_id: str
    storage_path: str
    created_at: datetime


class GenerateReportResponse(BaseModel):
    id: str
    run_id: str
    storage_path: str
    markdown_path: str
    html_path: str
    markdown_content: str
    html_content: str
    created_at: datetime


@reports_router.post("/runs/{run_id}/report", response_model=GenerateReportResponse)
def generate_run_report(
    run_id: str,
    req: GenerateReportRequest = GenerateReportRequest(),
    db: Session = Depends(get_db),
):
    """Generate a comprehensive analytical report in Markdown and HTML and save to storage."""
    uid = _parse_uuid(run_id)
    run = db.query(AnalysisRun).filter(AnalysisRun.id == uid).first() if uid else None
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AnalysisRun with ID '{run_id}' not found.",
        )

    version = db.query(DatasetVersion).filter(DatasetVersion.id == run.dataset_version_id).first()
    dataset = db.query(Dataset).filter(Dataset.id == version.dataset_id).first() if version else None
    dataset_name = dataset.name if dataset else "Dataset Analysis"

    # Gather data components
    # 1. Briefing if available in profile_json
    briefing_obj = None
    if run.profile_json and "briefing" in run.profile_json:
        try:
            briefing_obj = DatasetBriefing.model_validate(run.profile_json["briefing"])
        except Exception:
            pass

    # 2. Findings
    findings_query = db.query(DBFinding).filter(DBFinding.run_id == run.id)
    if req.include_pinned_only:
        findings_query = findings_query.filter(DBFinding.is_pinned == True)
    findings = findings_query.all()
    findings_payload = [
        {
            "id": str(f.id),
            "claim": f.claim,
            "evidence_json": f.evidence_json or [],
            "evidence_strength": f.evidence_strength,
            "source_columns": f.source_columns or [],
            "is_pinned": f.is_pinned,
            "user_notes": f.user_notes,
        }
        for f in findings
    ]

    # 3. Investigations
    investigations = db.query(Investigation).filter(Investigation.run_id == run.id).all()
    investigations_payload = [
        {
            "id": str(inv.id),
            "query": inv.query,
            "status": inv.status,
            "findings_count": inv.findings_count,
            "summary": inv.summary,
        }
        for inv in investigations
    ]

    # 4. Evidence Ledger aggregated across findings
    evidence_ledger = []
    seen_ev_ids = set()
    for f in findings:
        for ev in (f.evidence_json or []):
            ev_id = ev.get("id") or str(uuid.uuid4())
            if ev_id not in seen_ev_ids:
                seen_ev_ids.add(ev_id)
                evidence_ledger.append(ev)

    config = ReportConfig(
        title=req.title or f"Analysis Report: {dataset_name}",
        include_briefing=req.include_briefing,
        include_findings=req.include_findings,
        include_pinned_only=req.include_pinned_only,
        include_investigations=req.include_investigations,
        include_evidence_ledger=req.include_evidence_ledger,
        include_visualizations=req.include_visualizations,
    )

    generator = ReportGenerator(
        dataset_name=dataset_name,
        briefing=briefing_obj,
        findings=findings_payload,
        investigations=investigations_payload,
        evidence_ledger=evidence_ledger,
        config=config,
    )

    storage = get_storage_client()
    saved = generator.generate_and_save(run_id=str(run.id), storage_client=storage)

    # Save to database
    report_id = uuid.uuid4()
    db_report = DBReport(
        id=report_id,
        run_id=run.id,
        storage_path=saved["html_path"],
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return GenerateReportResponse(
        id=str(db_report.id),
        run_id=str(db_report.run_id),
        storage_path=db_report.storage_path,
        markdown_path=saved["markdown_path"],
        html_path=saved["html_path"],
        markdown_content=saved["markdown_content"],
        html_content=saved["html_content"],
        created_at=db_report.created_at,
    )


@reports_router.get("/runs/{run_id}/reports", response_model=List[ReportItemResponse])
def list_run_reports(
    run_id: str,
    db: Session = Depends(get_db),
):
    """List all generated reports for a run."""
    uid = _parse_uuid(run_id)
    if not uid:
        return []

    reports = db.query(DBReport).filter(DBReport.run_id == uid).order_by(DBReport.created_at.desc()).all()
    return [
        ReportItemResponse(
            id=str(r.id),
            run_id=str(r.run_id),
            storage_path=r.storage_path,
            created_at=r.created_at,
        )
        for r in reports
    ]


@reports_router.get("/reports/{report_id}", response_model=GenerateReportResponse)
def get_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full report content and metadata from storage."""
    rid = _parse_uuid(report_id)
    report = db.query(DBReport).filter(DBReport.id == rid).first() if rid else None
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )

    storage = get_storage_client()
    try:
        html_bytes = storage.download_bytes(report.storage_path)
        html_content = html_bytes.decode("utf-8") if html_bytes else ""
    except Exception:
        html_content = ""

    md_path = report.storage_path.replace(".html", ".md")
    try:
        md_bytes = storage.download_bytes(md_path)
        md_content = md_bytes.decode("utf-8") if md_bytes else ""
    except Exception:
        md_content = ""

    return GenerateReportResponse(
        id=str(report.id),
        run_id=str(report.run_id),
        storage_path=report.storage_path,
        markdown_path=md_path,
        html_path=report.storage_path,
        markdown_content=md_content,
        html_content=html_content,
        created_at=report.created_at,
    )
