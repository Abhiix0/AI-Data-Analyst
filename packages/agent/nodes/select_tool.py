"""Node for selecting the appropriate analytical tool and parameters."""
from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from packages.agent.state import AgentState, ToolCallRecord
from packages.agent.tool_registry import registry
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class ToolSelectionSchema(BaseModel):
    tool_name: str = Field(..., description="Registered tool name to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary conforming to the tool's input schema")


def select_tool_node(state: AgentState, llm: Optional[BaseLLMProvider] = None) -> AgentState:
    """Choose the best deterministic tool to execute for the current plan step."""
    if state.current_step_index >= len(state.plan_steps):
        state.pending_tool_call = None
        return state

    current_step = state.plan_steps[state.current_step_index]
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in registry.list_tools()])

    if llm and not hasattr(llm, "canned_responses"):
        try:
            prompt = (
                f"You are selecting an analytics tool to execute.\n"
                f"User Question: {state.question}\n"
                f"Current Step: {current_step}\n"
                f"Schema: {state.schema_info}\n"
                f"Available Tools:\n{tools_desc}\n\n"
                "Select the single most relevant tool and provide exact arguments (do NOT include 'df' or 'parquet_path' in arguments)."
            )
            result = llm.generate_structured(
                messages=[LLMMessage(role="user", content=prompt)],
                schema=ToolSelectionSchema,
            )
            if registry.get_tool(result.tool_name):
                state.pending_tool_call = ToolCallRecord(
                    tool_name=result.tool_name,
                    arguments=result.arguments,
                )
                return state
        except Exception:
            pass

    # Heuristic tool selection
    step_lower = current_step.lower()
    cols = state.target_columns

    if "compare segments" in step_lower or "segment" in step_lower:
        if len(cols) >= 2:
            state.pending_tool_call = ToolCallRecord(
                tool_name="compare_segments",
                arguments={"segment_column": cols[0], "metric_column": cols[1]},
            )
        elif cols:
            state.pending_tool_call = ToolCallRecord(
                tool_name="describe_column",
                arguments={"column": cols[0]},
            )
    elif "correlation" in step_lower:
        state.pending_tool_call = ToolCallRecord(
            tool_name="calculate_correlation",
            arguments={"limit": 10},
        )
    elif "outlier" in step_lower or "anomaly" in step_lower:
        if cols:
            state.pending_tool_call = ToolCallRecord(
                tool_name="detect_outliers",
                arguments={"column": cols[0]},
            )
    elif "trend" in step_lower:
        if len(cols) >= 2:
            state.pending_tool_call = ToolCallRecord(
                tool_name="find_trends",
                arguments={"time_column": cols[0], "metric_column": cols[1]},
            )
        elif cols:
            state.pending_tool_call = ToolCallRecord(
                tool_name="describe_column",
                arguments={"column": cols[0]},
            )
    elif "distribution" in step_lower or "describe" in step_lower:
        if cols:
            state.pending_tool_call = ToolCallRecord(
                tool_name="describe_column",
                arguments={"column": cols[0]},
            )
        else:
            state.pending_tool_call = ToolCallRecord(
                tool_name="calculate_missingness",
                arguments={},
            )
    elif "hypothesis" in step_lower:
        if len(cols) >= 2:
            state.pending_tool_call = ToolCallRecord(
                tool_name="test_hypothesis",
                arguments={"hypothesis_type": "correlation", "columns": cols[:2]},
            )
    else:
        # Fallback to describe or run_sql or calculate_missingness
        if cols:
            state.pending_tool_call = ToolCallRecord(
                tool_name="describe_column",
                arguments={"column": cols[0]},
            )
        else:
            state.pending_tool_call = ToolCallRecord(
                tool_name="calculate_missingness",
                arguments={},
            )

    return state
