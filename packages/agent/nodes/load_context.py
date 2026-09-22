"""Node for loading schema and dataset context into AgentState."""
from __future__ import annotations
import polars as pl
from packages.agent.state import AgentState
from packages.agent.tool_registry import registry


def load_context_node(state: AgentState) -> AgentState:
    """Load schema information and initial sample records if not already present."""
    if not state.schema_info:
        df = pl.read_parquet(state.parquet_path)
        schema_items = {col: str(dtype) for col, dtype in df.schema.items()}
        state.schema_info = schema_items

        # Sample rows for context
        sample_df = df.head(5)
        state.sample_records = [
            {k: (str(v) if v is not None else None) for k, v in row.items()}
            for row in sample_df.iter_rows(named=True)
        ]

        total_rows = len(df)
        total_cols = len(df.columns)
        state.dataset_summary = f"Dataset contains {total_rows} rows and {total_cols} columns: {', '.join(df.columns[:10])}{'...' if total_cols > 10 else ''}"

    return state
