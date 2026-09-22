"""Node for executing deterministic analytics tools and ledgering evidence."""
from __future__ import annotations
import uuid
from typing import Any, Dict
import polars as pl
from pydantic import BaseModel

from packages.agent.state import AgentState, ToolCallRecord
from packages.agent.tool_registry import registry
from packages.evidence.models import Evidence


def execute_tool_node(state: AgentState) -> AgentState:
    """Execute the pending tool call and record the resulting evidence into the ledger."""
    tool_call = state.pending_tool_call
    if not tool_call:
        return state

    df = pl.read_parquet(state.parquet_path)
    tool_name = tool_call.tool_name
    args = tool_call.arguments or {}

    try:
        raw_result = registry.execute(
            name=tool_name,
            df=df,
            parquet_path=state.parquet_path,
            **args,
        )
        tool_call.status = "success"

        # Convert raw_result into json/dict value
        if isinstance(raw_result, BaseModel):
            val_data = raw_result.model_dump()
        elif isinstance(raw_result, list):
            val_data = [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in raw_result
            ]
        elif isinstance(raw_result, dict):
            val_data = raw_result
        else:
            val_data = {"result": raw_result}

        evidence = Evidence(
            metric_name=f"{tool_name}_result",
            value=val_data,
            source_tool=tool_name,
            source_query=f"{tool_name}({args})",
            confidence_score=1.0,
        )
        state.evidence_ledger.append(evidence)

    except Exception as e:
        tool_call.status = "error"
        tool_call.error_message = str(e)
        state.errors.append(f"Tool {tool_name} error: {str(e)}")

    state.executed_tool_calls.append(tool_call)
    state.pending_tool_call = None
    return state
