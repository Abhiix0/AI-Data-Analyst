"""Unit tests for Visualization Engine, ChartSpec, Plotly rendering, and auto-selector."""
import os
import tempfile
import polars as pl
import pytest
import plotly.graph_objects as go

from packages.visualization.models import ChartSpec
from packages.visualization.renderer import to_plotly_figure, to_json_spec, to_html
from packages.visualization.selector import generate_chart_specs_from_df, generate_chart_specs_from_profile
from packages.agent.nodes.create_visualization import create_visualization_node
from packages.agent.state import AgentState


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "dept": ["Eng", "Eng", "Sales", "Sales", "HR"] * 10,
        "salary": [100.0, 110.0, 90.0, 95.0, 80.0] * 10,
        "tenure": [1, 2, 3, 4, 5] * 10,
    })


def test_chart_spec_serialization():
    spec = ChartSpec(
        chart_type="bar",
        title="Department Count",
        x="dept",
        y="count",
        data=[{"dept": "Eng", "count": 20}, {"dept": "Sales", "count": 20}],
    )
    json_str = to_json_spec(spec)
    assert "Department Count" in json_str
    assert "bar" in json_str


def test_plotly_rendering(sample_df):
    specs = [
        ChartSpec(chart_type="bar", title="Bar Chart", x="dept", y="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="line", title="Line Chart", x="tenure", y="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="scatter", title="Scatter Chart", x="tenure", y="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="box", title="Box Chart", x="dept", y="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="histogram", title="Histogram", x="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="pie", title="Pie Chart", x="dept", y="salary", data=sample_df.to_dicts()[:10]),
        ChartSpec(chart_type="heatmap", title="Heatmap", options={"z": [[1.0, 0.5], [0.5, 1.0]], "x_labels": ["A", "B"], "y_labels": ["A", "B"]}),
    ]

    for spec in specs:
        fig = to_plotly_figure(spec)
        assert isinstance(fig, go.Figure)
        html = to_html(spec)
        assert "<div id=" in html or "plotly" in html


def test_auto_chart_selector(sample_df):
    specs = generate_chart_specs_from_df(sample_df)
    assert len(specs) >= 2
    types = [s.chart_type for s in specs]
    assert "bar" in types or "histogram" in types


def test_create_visualization_node(sample_df):
    temp_dir = tempfile.mkdtemp()
    try:
        parquet_path = os.path.join(temp_dir, "data.parquet")
        sample_df.write_parquet(parquet_path)

        state = AgentState(
            question="Compare salaries across depts",
            parquet_path=parquet_path,
            target_columns=["dept", "salary"],
        )

        visuals = create_visualization_node(state)
        assert len(visuals) >= 1
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
