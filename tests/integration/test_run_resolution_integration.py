"""Integration tests verifying upload, chat, and report flow using dataset ID with run resolution."""
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from apps.api.app.core.database import get_db
from apps.api.app.models import Base, AnalysisRun, Dataset


@pytest.fixture
def test_db():
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
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_upload_then_chat_and_report_using_dataset_id_with_no_prior_ask(client, test_db):
    # 1. Upload dataset fixture
    csv_content = (
        "department,salary,experience,bonus\n"
        "Engineering,120000,5,15000\n"
        "Engineering,135000,7,18000\n"
        "Marketing,85000,3,8000\n"
        "Marketing,92000,4,9500\n"
        "Sales,95000,5,12000\n"
        "Sales,105000,6,14000\n"
    )
    file_tuple = ("employees.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    upload_res = client.post("/api/datasets", files={"file": file_tuple})
    assert upload_res.status_code == 201
    upload_data = upload_res.json()

    # Assert nested response shape
    assert "id" in upload_data
    dataset_id = upload_data["id"]
    assert upload_data["name"] == "employees"
    assert "latest_version" in upload_data
    assert upload_data["latest_version"] is not None
    assert upload_data["latest_version"]["row_count"] == 6
    assert upload_data["latest_version"]["col_count"] == 4

    # Verify an initial AnalysisRun was created during ingestion with the briefing
    runs_before = test_db.query(AnalysisRun).all()
    assert len(runs_before) == 1
    initial_run = runs_before[0]
    assert initial_run.profile_json is not None
    assert "briefing" in initial_run.profile_json

    # 2. Call GET /api/datasets/{dataset_id}/briefing and assert real findings/recommendations
    briefing_res = client.get(f"/api/datasets/{dataset_id}/briefing")
    assert briefing_res.status_code == 200, f"Expected 200, got {briefing_res.status_code}: {briefing_res.text}"
    briefing_data = briefing_res.json()
    assert briefing_data["title"] == "Dataset Executive Briefing"
    assert briefing_data["row_count"] == 6
    assert briefing_data["column_count"] == 4
    assert len(briefing_data["summary"]) > 0
    assert isinstance(briefing_data["findings"], list)
    assert len(briefing_data["findings"]) > 0
    assert isinstance(briefing_data["recommendations"], list)
    assert len(briefing_data["recommendations"]) > 0
    assert isinstance(briefing_data["recommended_charts"], list)
    assert len(briefing_data["recommended_charts"]) > 0

    # 3. Call POST /api/runs/{dataset_id}/chat with NO prior /ask call
    chat_res = client.post(
        f"/api/runs/{dataset_id}/chat",
        json={"message": "What is the average salary by department?"},
    )
    assert chat_res.status_code == 200, f"Expected 200, got {chat_res.status_code}: {chat_res.text}"
    chat_data = chat_res.json()
    assert chat_data["turn_index"] == 0
    assert len(chat_data["assistant_message"]) > 0

    # Verify that chat continued on the existing AnalysisRun
    runs_after_chat = test_db.query(AnalysisRun).all()
    assert len(runs_after_chat) == 1
    created_run = runs_after_chat[0]
    assert str(created_run.id) == chat_data["run_id"]

    # 3. Immediately call POST /api/runs/{dataset_id}/report with NO prior /ask call
    report_res = client.post(
        f"/api/runs/{dataset_id}/report",
        json={"title": "Department Salary Report", "include_pinned_only": False},
    )
    assert report_res.status_code == 200, f"Expected 200, got {report_res.status_code}: {report_res.text}"
    report_data = report_res.json()
    assert report_data["run_id"] == str(created_run.id)
    assert len(report_data["html_content"]) > 0
    assert len(report_data["markdown_content"]) > 0

    # 4. Verify GET /api/runs/{dataset_id}/findings and investigations work seamlessly
    findings_res = client.get(f"/api/runs/{dataset_id}/findings")
    assert findings_res.status_code == 200
    assert isinstance(findings_res.json(), list)

    inv_res = client.get(f"/api/runs/{dataset_id}/investigations")
    assert inv_res.status_code == 200
    assert isinstance(inv_res.json(), list)

    history_res = client.get(f"/api/runs/{dataset_id}/chat/history")
    assert history_res.status_code == 200
    assert len(history_res.json()) == 1

    reports_list_res = client.get(f"/api/runs/{dataset_id}/reports")
    assert reports_list_res.status_code == 200
    assert len(reports_list_res.json()) >= 1
