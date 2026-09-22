"""Unit tests for Report Generation Engine (Phase 15)."""
import os
import shutil
import tempfile
import uuid
import polars as pl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Base,
    User,
    Dataset,
    DatasetVersion,
    AnalysisRun,
    Finding,
    Investigation,
    Report,
)
from packages.analytics.briefing import generate_briefing
from packages.analytics.reports import ReportConfig, ReportGenerator
from packages.shared.storage import LocalDiskStorageClient


@pytest.fixture
def storage_temp(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", temp_dir)
    storage = LocalDiskStorageClient(base_dir=temp_dir)
    yield storage
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db_session):
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_report_generator_direct_markdown_and_html(storage_temp):
    df = pl.DataFrame({
        "revenue": [100.0, 200.0, 300.0, 400.0, 500.0],
        "category": ["A", "B", "A", "B", "A"],
    })
    briefing = generate_briefing(df)

    generator = ReportGenerator(
        dataset_name="Test Revenue Dataset",
        briefing=briefing,
        findings=[
            {
                "claim": "Category A generates 60% of total revenue.",
                "evidence_strength": "strong",
                "source_columns": ["revenue", "category"],
                "evidence_json": [{"metric_name": "revenue_share", "value": 0.60, "confidence_score": 1.0}],
                "is_pinned": True,
            }
        ],
        investigations=[
            {
                "query": "Investigate revenue variance across quarters",
                "summary": "Revenue variance is driven by cyclical seasonality.",
                "findings_count": 2,
                "status": "completed",
            }
        ],
        evidence_ledger=[
            {
                "id": str(uuid.uuid4()),
                "metric_name": "revenue_share",
                "value": 0.60,
                "source_tool": "compare_segments",
                "confidence_score": 1.0,
            }
        ],
    )

    md = generator.generate_markdown()
    assert "# AI Data Analyst — Analytical Report" in md
    assert "Test Revenue Dataset" in md
    assert "Category A generates 60% of total revenue." in md
    assert "Investigate revenue variance across quarters" in md
    assert "Verified Evidence Ledger" in md

    html = generator.generate_html()
    assert "<!DOCTYPE html>" in html
    assert "Category A generates 60% of total revenue." in html
    assert "container" in html

    saved = generator.generate_and_save(run_id="run_123", storage_client=storage_temp)
    assert "markdown_path" in saved
    assert "html_path" in saved
    assert storage_temp.exists(saved["markdown_path"]) is True
    assert storage_temp.exists(saved["html_path"]) is True


def test_report_api_endpoints(client, test_db_session, storage_temp):
    u_id = uuid.uuid4()
    d_id = uuid.uuid4()
    v_id = uuid.uuid4()
    r_id = uuid.uuid4()
    f_id = uuid.uuid4()

    user = User(id=u_id, email="report@example.com")
    dataset = Dataset(id=d_id, user_id=u_id, name="Financial Health")
    version = DatasetVersion(
        id=v_id,
        dataset_id=d_id,
        row_count=50,
        col_count=3,
        storage_path="datasets/dummy.parquet",
    )
    run = AnalysisRun(
        id=r_id,
        dataset_version_id=v_id,
        status="completed",
        profile_json={},
    )
    finding = Finding(
        id=f_id,
        run_id=r_id,
        claim="Operating margins increased by 14% year-over-year.",
        evidence_json=[{"metric_name": "margin_growth", "value": 0.14, "confidence_score": 0.98}],
        evidence_strength="strong",
        source_columns=["operating_income", "revenue"],
        is_pinned=True,
    )

    test_db_session.add_all([user, dataset, version, run, finding])
    test_db_session.commit()

    # 1. Generate Report
    gen_resp = client.post(
        f"/api/runs/{r_id}/report",
        json={"title": "Q3 Executive Performance Report", "include_pinned_only": False},
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    rep_id = gen_data["id"]
    assert rep_id is not None
    assert "Operating margins increased" in gen_data["markdown_content"]
    assert "Q3 Executive Performance Report" in gen_data["html_content"]

    # 2. List reports for run
    list_resp = client.get(f"/api/runs/{r_id}/reports")
    assert list_resp.status_code == 200
    reports_list = list_resp.json()
    assert len(reports_list) == 1
    assert reports_list[0]["id"] == rep_id

    # 3. Get single report detail
    detail_resp = client.get(f"/api/reports/{rep_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == rep_id
    assert detail_data["html_content"] == gen_data["html_content"]
