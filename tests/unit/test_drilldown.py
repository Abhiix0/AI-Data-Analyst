"""Unit tests for Finding Drill-Down investigations."""
import os
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
from apps.api.app.models import Base, User, Dataset, DatasetVersion, AnalysisRun, Finding


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
def seeded_finding(test_db_session):
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "drilldown_data.parquet")
    df = pl.DataFrame({
        "id": list(range(1, 101)),
        "contract": ["Month-to-month"] * 50 + ["Two-year"] * 50,
        "churn": ["Yes"] * 40 + ["No"] * 60,
        "monthly_charges": [70.0 + i for i in range(100)],
    })
    df.write_parquet(parquet_path)

    u_id = uuid.uuid4()
    d_id = uuid.uuid4()
    v_id = uuid.uuid4()
    r_id = uuid.uuid4()
    f_id = uuid.uuid4()

    user = User(id=u_id, email="drilldown@example.com")
    dataset = Dataset(id=d_id, user_id=u_id, name="Churn Dataset")
    version = DatasetVersion(
        id=v_id,
        dataset_id=d_id,
        row_count=100,
        col_count=4,
        storage_path=parquet_path,
        schema_json={"contract": "String", "churn": "String", "monthly_charges": "Float64"},
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
        claim="Month-to-month contracts have 80% higher churn rate.",
        evidence_json=[{"metric_name": "churn_rate", "value": 0.8, "source_tool": "compare_segments", "confidence_score": 1.0}],
        evidence_strength="strong",
        source_columns=["contract", "churn"],
    )

    test_db_session.add_all([user, dataset, version, run, finding])
    test_db_session.commit()

    yield str(f_id)

    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_drilldown_investigation(client, seeded_finding):
    finding_id = seeded_finding

    resp = client.post(f"/api/findings/{finding_id}/investigate")
    assert resp.status_code == 200
    data = resp.json()

    assert data["parent_finding_id"] == finding_id
    assert "Month-to-month" in data["parent_claim"]
    assert len(data["answer"]) > 20
    assert len(data["evidence"]) >= 1
    assert len(data["new_findings"]) >= 1


def test_drilldown_nonexistent_finding(client):
    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/findings/{fake_id}/investigate")
    assert resp.status_code == 404
