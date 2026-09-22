"""Unit tests for tool registry and analytics tool functions."""
import os
import tempfile
import polars as pl
import pytest
from pydantic import BaseModel

from packages.agent.tool_registry import registry, ToolRegistry
from packages.analytics.tools.trends import find_trends
from packages.analytics.tools.segments import compare_segments
from packages.analytics.tools.grouping import group_by, aggregate
from packages.analytics.tools.filtering import filter_dataset


@pytest.fixture
def sample_dataset():
    return pl.DataFrame({
        "id": list(range(1, 101)),
        "dept": ["Engineering"] * 40 + ["Sales"] * 35 + ["HR"] * 25,
        "salary": [100000 + i * 500 for i in range(100)],
        "tenure": [1 + (i % 10) for i in range(100)],
        "churn": ["No"] * 80 + ["Yes"] * 20,
    })


def test_registry_schema_integrity():
    tools = registry.list_tools()
    assert len(tools) >= 17
    for tool in tools:
        assert issubclass(tool.input_schema, BaseModel)
        assert len(tool.description.strip()) > 10
        assert tool.name


def test_registry_execution_of_all_tools(sample_dataset):
    temp_dir = tempfile.mkdtemp()
    try:
        parquet_path = os.path.join(temp_dir, "data.parquet")
        sample_dataset.write_parquet(parquet_path)

        # 1. inspect_schema
        schema = registry.execute("inspect_schema", df=sample_dataset)
        assert len(schema) == 5

        # 2. get_column_metadata
        meta = registry.execute("get_column_metadata", df=sample_dataset, column="dept")
        assert meta.unique_count == 3

        # 3. get_unique_values (test capping)
        uniques = registry.execute("get_unique_values", df=sample_dataset, column="dept", limit=10)
        assert len(uniques.values) == 3

        # 4. get_sample_rows (test capping)
        samples = registry.execute("get_sample_rows", df=sample_dataset, n=5)
        assert len(samples.records) == 5

        # 5. describe_column
        stats = registry.execute("describe_column", df=sample_dataset, column="salary")
        assert stats.mean > 100000

        # 6. calculate_missingness
        missing = registry.execute("calculate_missingness", df=sample_dataset)
        assert isinstance(missing, dict)

        # 7. calculate_correlation
        corr = registry.execute("calculate_correlation", df=sample_dataset)
        assert len(corr) > 0

        # 8. detect_outliers
        outliers = registry.execute("detect_outliers", df=sample_dataset, column="salary")
        # perfectly uniform salary distribution has no IQR outliers
        assert outliers is None

        # 9. filter_dataset
        filtered = registry.execute("filter_dataset", df=sample_dataset, column="dept", operator="==", value="Engineering")
        assert filtered.matched_rows == 40

        # 10. group_by
        grouped = registry.execute("group_by", df=sample_dataset, group_column="dept", agg_column="salary", agg_fn="mean")
        assert len(grouped.groups) == 3

        # 11. aggregate
        agg = registry.execute("aggregate", df=sample_dataset, column="salary", agg_fn="sum")
        assert agg.value > 0

        # 12. compare_segments
        segs = registry.execute("compare_segments", df=sample_dataset, segment_column="dept", metric_column="salary")
        assert "Engineering" in segs.segments

        # 13. find_trends
        trend = registry.execute("find_trends", df=sample_dataset, time_column="id", metric_column="salary")
        assert trend.direction == "increasing"

        # 14. find_anomalies
        anomalies = registry.execute("find_anomalies", df=sample_dataset, column="salary", method="zscore")
        assert anomalies.column == "salary"

        # 15. test_hypothesis (correlation)
        hyp_corr = registry.execute("test_hypothesis", df=sample_dataset, hypothesis_type="correlation", columns=["id", "salary"])
        assert hyp_corr.significant is True

        # 16. test_hypothesis (t-test)
        hyp_ttest = registry.execute("test_hypothesis", df=sample_dataset, hypothesis_type="two_sample_ttest", columns=["churn", "salary"])
        assert hyp_ttest.test_name == "Welch's Two-Sample T-Test"

        # 17. run_sql
        sql_res = registry.execute("run_sql", parquet_path=parquet_path, sql="SELECT dept, COUNT(*) FROM dataset GROUP BY 1")
        assert len(sql_res.rows) == 3

        # 18. explain_sql
        explain_res = registry.execute("explain_sql", parquet_path=parquet_path, sql="SELECT dept, COUNT(*) FROM dataset GROUP BY 1")
        assert len(explain_res) > 0
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
