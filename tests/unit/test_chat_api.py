"""Unit tests for Conversational Chat API and Context Retention."""
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
from apps.api.app.models import Base, User, Dataset, DatasetVersion, AnalysisRun, ConversationTurn


@pytest.fixture
def test_db_session():
    # In-memory SQLite with StaticPool for fast isolated tests
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
def seeded_run(test_db_session):
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "chat_data.parquet")
    df = pl.DataFrame({
        "customer_id": [f"ID_{i}" for i in range(1, 51)],
        "gender": ["Male", "Female"] * 25,
        "monthly_charges": [50.0 + i for i in range(50)],
    })
    df.write_parquet(parquet_path)

    u_id = uuid.uuid4()
    d_id = uuid.uuid4()
    v_id = uuid.uuid4()
    r_id = uuid.uuid4()

    user = User(id=u_id, email="chat_test@example.com")
    dataset = Dataset(id=d_id, user_id=u_id, name="Telco Test")
    version = DatasetVersion(
        id=v_id,
        dataset_id=d_id,
        row_count=50,
        col_count=3,
        storage_path=parquet_path,
        schema_json={"customer_id": "String", "gender": "String", "monthly_charges": "Float64"},
    )
    run = AnalysisRun(
        id=r_id,
        dataset_version_id=v_id,
        status="completed",
        profile_json={},
    )

    test_db_session.add_all([user, dataset, version, run])
    test_db_session.commit()

    yield str(r_id)

    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_chat_multi_turn_flow(client, seeded_run):
    run_id = seeded_run

    # Turn 1
    resp1 = client.post(
        f"/api/runs/{run_id}/chat",
        json={"message": "What is the average monthly charge?"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["turn_index"] == 0
    assert len(data1["assistant_message"]) > 20
    assert len(data1["evidence"]) >= 1

    # Turn 2 (Follow-up)
    resp2 = client.post(
        f"/api/runs/{run_id}/chat",
        json={"message": "What about when comparing across gender?"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["turn_index"] == 1

    # Fetch History
    hist_resp = client.get(f"/api/runs/{run_id}/chat/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    assert history[0]["turn_index"] == 0
    assert history[1]["turn_index"] == 1
