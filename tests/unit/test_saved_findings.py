"""Unit tests for Saved Findings, Notes, and Investigation History (Phase 14)."""
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
)


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


@pytest.fixture
def seeded_environment(test_db_session):
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "saved_findings_data.parquet")
    df = pl.DataFrame({
        "customer_id": list(range(1, 101)),
        "segment": ["Enterprise"] * 40 + ["SMB"] * 60,
        "mrr": [1200.0 + i * 10 for i in range(100)],
        "churned": [0] * 70 + [1] * 30,
    })
    df.write_parquet(parquet_path)

    u_id = uuid.uuid4()
    d_id = uuid.uuid4()
    v_id = uuid.uuid4()
    r_id = uuid.uuid4()
    f1_id = uuid.uuid4()
    f2_id = uuid.uuid4()

    user = User(id=u_id, email="saved_findings@example.com")
    dataset = Dataset(id=d_id, user_id=u_id, name="SaaS Metrics")
    version = DatasetVersion(
        id=v_id,
        dataset_id=d_id,
        row_count=100,
        col_count=4,
        storage_path=parquet_path,
        schema_json={"customer_id": "Int64", "segment": "String", "mrr": "Float64", "churned": "Int64"},
    )
    run = AnalysisRun(
        id=r_id,
        dataset_version_id=v_id,
        status="completed",
        profile_json={},
    )
    f1 = Finding(
        id=f1_id,
        run_id=r_id,
        claim="Enterprise customer segment accounts for 65% of total MRR.",
        evidence_json=[{"metric_name": "mrr_share", "value": 0.65, "confidence_score": 1.0}],
        evidence_strength="strong",
        source_columns=["segment", "mrr"],
        is_pinned=False,
    )
    f2 = Finding(
        id=f2_id,
        run_id=r_id,
        claim="SMB customers have a 30% higher churn rate.",
        evidence_json=[{"metric_name": "churn_rate", "value": 0.30, "confidence_score": 0.95}],
        evidence_strength="moderate",
        source_columns=["segment", "churned"],
        is_pinned=True,
        user_notes="Investigate why SMB churn spikes in Q3.",
    )

    test_db_session.add_all([user, dataset, version, run, f1, f2])
    test_db_session.commit()

    yield {
        "run_id": str(r_id),
        "f1_id": str(f1_id),
        "f2_id": str(f2_id),
    }

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_and_patch_finding(client, seeded_environment):
    f1_id = seeded_environment["f1_id"]

    # 1. Fetch initial state
    resp = client.get(f"/api/findings/{f1_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == f1_id
    assert data["is_pinned"] is False
    assert data["user_notes"] is None

    # 2. Patch to pin and add notes
    patch_resp = client.patch(
        f"/api/findings/{f1_id}",
        json={
            "is_pinned": True,
            "user_notes": "Crucial revenue concentration finding for board deck.",
        },
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["is_pinned"] is True
    assert patched_data["user_notes"] == "Crucial revenue concentration finding for board deck."

    # 3. Verify persistence
    get_resp2 = client.get(f"/api/findings/{f1_id}")
    assert get_resp2.status_code == 200
    assert get_resp2.json()["is_pinned"] is True
    assert get_resp2.json()["user_notes"] == "Crucial revenue concentration finding for board deck."


def test_list_run_findings_with_filters(client, seeded_environment):
    run_id = seeded_environment["run_id"]

    # All findings
    resp = client.get(f"/api/runs/{run_id}/findings")
    assert resp.status_code == 200
    all_findings = resp.json()
    assert len(all_findings) == 2

    # Pinned only filter
    pinned_resp = client.get(f"/api/runs/{run_id}/findings?is_pinned=true")
    assert pinned_resp.status_code == 200
    pinned = pinned_resp.json()
    assert len(pinned) == 1
    assert pinned[0]["id"] == seeded_environment["f2_id"]
    assert pinned[0]["is_pinned"] is True

    # Strength filter
    strong_resp = client.get(f"/api/runs/{run_id}/findings?strength=strong")
    assert strong_resp.status_code == 200
    strong = strong_resp.json()
    assert len(strong) == 1
    assert strong[0]["id"] == seeded_environment["f1_id"]


def test_investigation_creation_and_history(client, seeded_environment):
    run_id = seeded_environment["run_id"]
    f1_id = seeded_environment["f1_id"]

    # Trigger investigation
    inv_resp = client.post(f"/api/findings/{f1_id}/investigate")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    inv_id = inv_data["investigation_id"]
    assert inv_id is not None
    assert inv_data["parent_finding_id"] == f1_id

    # List investigations on run
    list_inv_resp = client.get(f"/api/runs/{run_id}/investigations")
    assert list_inv_resp.status_code == 200
    inv_list = list_inv_resp.json()
    assert len(inv_list) >= 1
    assert any(i["id"] == inv_id for i in inv_list)

    # Get single investigation detail
    get_inv_resp = client.get(f"/api/investigations/{inv_id}")
    assert get_inv_resp.status_code == 200
    inv_detail = get_inv_resp.json()
    assert inv_detail["id"] == inv_id
    assert inv_detail["run_id"] == run_id
    assert inv_detail["parent_finding_id"] == f1_id
    assert inv_detail["status"] == "completed"
    assert inv_detail["findings_count"] >= 1
    assert "result_json" in inv_detail
