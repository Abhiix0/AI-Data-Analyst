"""Node for generating ChartSpec visualizations from agent evidence and findings."""
from __future__ import annotations
from typing import List, Optional
import polars as pl

from packages.agent.state import AgentState
from packages.visualization.models import ChartSpec
from packages.visualization.selector import generate_chart_specs_from_df


def create_visualization_node(state: AgentState) -> List[ChartSpec]:
    """Generate visual ChartSpec objects corresponding to state findings and target columns."""
    if not state.parquet_path:
        return []

    try:
        df = pl.read_parquet(state.parquet_path)
        # If target columns specified, prioritize subset
        if state.target_columns:
            valid_cols = [c for c in state.target_columns if c in df.columns]
            if valid_cols:
                sub_df = df.select(valid_cols)
                return generate_chart_specs_from_df(sub_df, max_charts=4)
        return generate_chart_specs_from_df(df, max_charts=4)
    except Exception:
        return []
