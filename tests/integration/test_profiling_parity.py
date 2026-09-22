"""Integration tests verifying statistical outputs of Polars profiling tools."""
import os
import polars as pl
import pytest

from packages.analytics.tools import generate_profile

SAMPLE_DIR = os.path.join(os.getcwd(), "kaggle_downloads")


@pytest.mark.parametrize("filename", ["tested.csv", "WA_Fn-UseC_-Telco-Customer-Churn.csv"])
def test_profiling_pipeline_against_samples(filename):
    file_path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.isfile(file_path):
        pytest.skip(f"Sample dataset '{filename}' not found")

    pldf = pl.read_csv(file_path, ignore_errors=True)
    res = generate_profile(pldf)

    # 1. Structure integrity
    assert res["shape"]["rows"] > 0
    assert res["shape"]["columns"] > 0
    assert isinstance(res["missing"], dict)
    assert isinstance(res["numeric_stats"], dict)
    assert isinstance(res["top_correlations"], list)
    assert isinstance(res["highlights"], list)
    assert len(res["highlights"]) > 0

    # 2. Specific dataset checks for tested.csv
    if filename == "tested.csv":
        assert res["shape"]["rows"] == 418
        assert res["shape"]["columns"] == 12
        assert "Age" in res["numeric_stats"]
        assert res["numeric_stats"]["Age"]["null_count"] == 86
