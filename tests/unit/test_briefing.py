"""Unit tests for Dataset Briefing and Proactive Discovery Engine."""
import uuid
import polars as pl
import pytest

from packages.analytics.briefing import generate_briefing, DatasetBriefing


@pytest.fixture
def briefing_sample_df():
    return pl.DataFrame({
        "customer_id": [f"C_{i}" for i in range(1, 101)],
        "tenure": [i % 20 for i in range(100)],
        "monthly_charges": [20.0 + i * 2.0 for i in range(100)],
        "total_charges": [(20.0 + i * 2.0) * (i % 20) for i in range(100)],
        "optional_service": ["Yes" if i % 2 == 0 else None for i in range(100)],  # 50% missing
        "skewed_metric": [10.0] * 95 + [5000.0] * 5,  # Outliers & heavy skew
    })


def test_generate_briefing_structure(briefing_sample_df):
    v_id = uuid.uuid4()
    briefing = generate_briefing(df=briefing_sample_df, dataset_version_id=v_id)

    assert isinstance(briefing, DatasetBriefing)
    assert briefing.row_count == 100
    assert briefing.column_count == 6
    assert "100 records" in briefing.summary
    assert len(briefing.findings) >= 1
    assert len(briefing.recommendations) >= 1
    assert len(briefing.recommended_charts) >= 1

    # Verify all findings are typed with evidence
    for finding in briefing.findings:
        assert finding.claim
        assert len(finding.evidence) >= 1
        assert finding.evidence_strength in ("strong", "moderate", "weak", "insufficient")
        assert finding.dataset_version_id == v_id
