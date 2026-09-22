"""Unit tests for SQLAlchemy models structure and instantiation."""
import uuid
from apps.api.app.models import (
    User,
    Dataset,
    DatasetVersion,
    AnalysisRun,
    Finding,
    Report,
)


def test_model_instantiation():
    user = User(email="analyst@example.com")
    assert user.email == "analyst@example.com"

    dataset = Dataset(user=user, name="Sales Data")
    assert dataset.name == "Sales Data"
    assert dataset.user == user

    version = DatasetVersion(
        dataset=dataset,
        storage_path="datasets/v1/data.parquet",
        row_count=1000,
        col_count=10,
        schema_json={"columns": ["id", "revenue"]},
    )
    assert version.row_count == 1000
    assert version.dataset == dataset

    run = AnalysisRun(
        dataset_version=version,
        status="completed",
    )
    assert run.status == "completed"
    assert run.dataset_version == version

    finding = Finding(
        run=run,
        claim="Revenue correlates strongly with ad spend (r=0.85).",
        evidence_json=[
            {
                "metric_name": "correlation",
                "value": 0.85,
                "source_tool": "calculate_correlation",
                "source_columns": ["revenue", "ad_spend"],
            }
        ],
        evidence_strength="strong",
        source_columns=["revenue", "ad_spend"],
    )
    assert finding.evidence_strength == "strong"
    assert len(finding.evidence_json) == 1

    report = Report(
        run=run,
        storage_path="reports/run_1/report.md",
    )
    assert report.run == run
