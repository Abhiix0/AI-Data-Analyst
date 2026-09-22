"""Unit tests for LangGraph Analytical Agent and Evidence Validation Gate."""
import os
import tempfile
import polars as pl
import pytest

from packages.agent.graph import build_analytical_graph, run_analytical_agent
from packages.agent.nodes.load_context import load_context_node
from packages.agent.nodes.understand_question import understand_question_node
from packages.agent.nodes.create_plan import create_plan_node
from packages.agent.nodes.select_tool import select_tool_node
from packages.agent.nodes.execute_tool import execute_tool_node
from packages.agent.nodes.synthesize_finding import synthesize_finding_node
from packages.agent.nodes.validate_evidence import validate_evidence_node
from packages.agent.state import AgentState, ToolCallRecord
from packages.evidence.models import Evidence, Finding
from packages.shared.llm_provider import MockLLMProvider, LLMMessage, BaseLLMProvider


@pytest.fixture
def sample_parquet():
    temp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(temp_dir, "test_dataset.parquet")
    df = pl.DataFrame({
        "customer_id": [f"CUST_{i}" for i in range(1, 101)],
        "churn": ["No"] * 75 + ["Yes"] * 25,
        "monthly_charges": [20.0 + i * 1.5 for i in range(100)],
        "tenure_months": [1 + (i % 24) for i in range(100)],
    })
    df.write_parquet(parquet_path)
    yield parquet_path
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_mock_llm_provider():
    provider = MockLLMProvider({"greeting": "Hello Analyst!"})
    resp = provider.generate([LLMMessage(role="user", content="say greeting")])
    assert resp.content == "Hello Analyst!"


def test_load_context_node(sample_parquet):
    state = AgentState(
        question="What is the distribution of monthly charges?",
        parquet_path=sample_parquet,
    )
    new_state = load_context_node(state)
    assert "monthly_charges" in new_state.schema_info
    assert len(new_state.sample_records) == 5
    assert "100 rows" in new_state.dataset_summary


def test_understand_and_plan_nodes(sample_parquet):
    state = AgentState(
        question="Compare monthly_charges by churn status",
        parquet_path=sample_parquet,
    )
    state = load_context_node(state)
    state = understand_question_node(state)
    assert len(state.target_columns) >= 1

    state = create_plan_node(state)
    assert len(state.plan_steps) >= 1
    assert state.current_step_index == 0


def test_tool_selection_and_execution(sample_parquet):
    state = AgentState(
        question="Analyze monthly_charges distribution",
        parquet_path=sample_parquet,
    )
    state = load_context_node(state)
    state = understand_question_node(state)
    state = create_plan_node(state)

    state = select_tool_node(state)
    assert state.pending_tool_call is not None
    assert state.pending_tool_call.tool_name

    state = execute_tool_node(state)
    assert len(state.evidence_ledger) >= 1
    assert state.pending_tool_call is None
    assert len(state.executed_tool_calls) == 1
    assert state.executed_tool_calls[0].status == "success"


def test_validate_evidence_gate_passes_grounded_numbers():
    evidence = Evidence(
        metric_name="describe_column_result",
        value={"mean": 94.25, "std": 12.8, "min": 20.0, "max": 168.5},
        source_tool="describe_column",
        source_query="describe_column(monthly_charges)",
        confidence_score=1.0,
    )
    finding = Finding(
        title="Monthly charges mean",
        description="The mean monthly charges is 94.25 with max of 168.5",
        category="distribution",
        evidence_strength="strong",
        evidence_ids=[str(evidence.id)],
    )

    state = AgentState(
        question="What is the average charge?",
        parquet_path="dummy.parquet",
        evidence_ledger=[evidence],
        synthesized_findings=[finding],
        draft_answer="The average monthly charge observed was 94.25.",
    )

    state = validate_evidence_node(state)
    assert state.validation_passed is True
    assert "passed" in state.validation_notes[0].lower()


def test_validate_evidence_gate_catches_hallucinations():
    evidence = Evidence(
        metric_name="describe_column_result",
        value={"mean": 94.25, "std": 12.8},
        source_tool="describe_column",
        source_query="describe_column(monthly_charges)",
        confidence_score=1.0,
    )
    # Hallucinated number 999.88 not present in evidence
    finding = Finding(
        title="Hallucinated finding",
        description="The projected loss is 999.88 per customer.",
        category="trend",
        evidence_strength="strong",
        evidence_ids=[str(evidence.id)],
    )

    state = AgentState(
        question="What is the average charge?",
        parquet_path="dummy.parquet",
        evidence_ledger=[evidence],
        synthesized_findings=[finding],
        draft_answer="The system detected a severe anomaly of 999.88 in monthly charges.",
    )

    state = validate_evidence_node(state)
    assert state.validation_passed is False
    assert any("unsubstantiated" in note.lower() for note in state.validation_notes)


def test_end_to_end_agent_graph_execution(sample_parquet):
    final_state = run_analytical_agent(
        question="Compare monthly_charges by churn",
        parquet_path=sample_parquet,
    )

    assert final_state.completed is True
    assert len(final_state.evidence_ledger) >= 1
    assert len(final_state.synthesized_findings) >= 1
    assert len(final_state.final_response) > 50
    assert "Evidence" in final_state.final_response
