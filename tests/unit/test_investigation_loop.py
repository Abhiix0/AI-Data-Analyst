"""Unit tests for investigation loop, follow-up drilling, and tool-call deduplication."""
import os
import tempfile
import polars as pl
import pytest

from packages.agent.nodes.create_followup import create_followup_node
from packages.agent.nodes.execute_tool import execute_tool_node
from packages.agent.state import AgentState, ToolCallRecord
from packages.evidence.models import Evidence, Finding
from packages.shared.llm_provider import MockLLMProvider


@pytest.fixture
def sample_dataset_path():
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "churn_data.parquet")
    df = pl.DataFrame({
        "customer_id": [f"ID_{i}" for i in range(1, 101)],
        "contract_type": ["Month-to-month"] * 50 + ["One year"] * 30 + ["Two year"] * 20,
        "churn": ["Yes"] * 40 + ["No"] * 60,
        "monthly_charges": [50.0 + i for i in range(100)],
    })
    df.write_parquet(parquet_path)
    yield parquet_path
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_tool_call_deduplication(sample_dataset_path):
    state = AgentState(
        question="Check charges",
        parquet_path=sample_dataset_path,
        pending_tool_call=ToolCallRecord(
            tool_name="describe_column",
            arguments={"column": "monthly_charges"},
        ),
    )

    # 1. First execution
    state = execute_tool_node(state)
    assert len(state.executed_tool_calls) == 1
    assert state.executed_tool_calls[0].status == "success"
    assert len(state.evidence_ledger) == 1

    # 2. Second identical execution
    state.pending_tool_call = ToolCallRecord(
        tool_name="describe_column",
        arguments={"column": "monthly_charges"},
    )
    state = execute_tool_node(state)
    assert len(state.executed_tool_calls) == 2
    assert state.executed_tool_calls[1].status == "cached"
    # Evidence ledger length should still be 1 (no duplicate evidence added)
    assert len(state.evidence_ledger) == 1


def test_followup_depth_and_bounding():
    evidence = Evidence(
        metric_name="segment_result",
        value={"Month-to-month": {"mean": 85.0}, "Two year": {"mean": 45.0}},
        source_tool="compare_segments",
        confidence_score=1.0,
    )
    finding = Finding(
        title="High churn in Month-to-month",
        description="Month-to-month users have higher mean charges of 85.0.",
        category="segment",
        evidence_strength="strong",
        evidence_ids=[str(evidence.id)],
    )

    state = AgentState(
        question="Why is churn high?",
        parquet_path="dummy.parquet",
        evidence_ledger=[evidence],
        synthesized_findings=[finding],
        plan_steps=["Step 1"],
        current_step_index=1,
        iteration_count=0,
        max_iterations=10,
    )

    # Mock provider returning follow-up recommendation
    mock_llm = MockLLMProvider({
        "reviewing intermediate findings": {
            "should_investigate": True,
            "followup_steps": ["Analyze contract_type with payment_method"],
            "rationale": "High variance across contract types",
        }
    })

    new_state = create_followup_node(state, llm=mock_llm)
    assert len(new_state.plan_steps) == 2
    assert "payment_method" in new_state.plan_steps[1]


def test_followup_stops_at_max_iterations():
    state = AgentState(
        question="Why is churn high?",
        parquet_path="dummy.parquet",
        plan_steps=["Step 1", "Step 2"],
        current_step_index=2,
        iteration_count=10,
        max_iterations=10,
    )

    mock_llm = MockLLMProvider({
        "reviewing": {
            "should_investigate": True,
            "followup_steps": ["Another step"],
        }
    })

    new_state = create_followup_node(state, llm=mock_llm)
    assert len(new_state.plan_steps) == 2  # No new steps added because max iterations reached
