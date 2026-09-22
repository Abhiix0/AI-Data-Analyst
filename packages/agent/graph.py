"""LangGraph implementation of the Analytical Agent."""
from __future__ import annotations
from typing import Optional
from langgraph.graph import StateGraph, END, START

from packages.agent.state import AgentState
from packages.agent.nodes.load_context import load_context_node
from packages.agent.nodes.understand_question import understand_question_node
from packages.agent.nodes.create_plan import create_plan_node
from packages.agent.nodes.select_tool import select_tool_node
from packages.agent.nodes.execute_tool import execute_tool_node
from packages.agent.nodes.inspect_result import inspect_result_node
from packages.agent.nodes.synthesize_finding import synthesize_finding_node
from packages.agent.nodes.validate_evidence import validate_evidence_node
from packages.agent.nodes.create_followup import create_followup_node
from packages.agent.nodes.final_response import final_response_node
from packages.shared.llm_provider import BaseLLMProvider, get_llm_provider


def should_continue_tool_execution(state: AgentState) -> str:
    """Route: determine if another tool step is needed or proceed to synthesis."""
    if state.current_step_index < len(state.plan_steps) and state.iteration_count < state.max_iterations:
        return "select_tool"
    return "synthesize_finding"


def route_after_validation(state: AgentState) -> str:
    """Route: determine if evidence validation passed, need follow-up, or retry synthesis."""
    if not state.validation_passed and state.validation_attempts < 2:
        return "synthesize_finding"
    if state.validation_passed and state.current_step_index < len(state.plan_steps) and state.iteration_count < state.max_iterations:
        return "select_tool"
    return "final_response"


def build_analytical_graph(llm: Optional[BaseLLMProvider] = None) -> StateGraph:
    """Build and compile the LangGraph analytical agent workflow."""
    provider = llm or get_llm_provider()

    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("understand_question", lambda state: understand_question_node(state, llm=provider))
    workflow.add_node("create_plan", lambda state: create_plan_node(state, llm=provider))
    workflow.add_node("select_tool", lambda state: select_tool_node(state, llm=provider))
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("inspect_result", inspect_result_node)
    workflow.add_node("synthesize_finding", lambda state: synthesize_finding_node(state, llm=provider))
    workflow.add_node("validate_evidence", validate_evidence_node)
    workflow.add_node("create_followup", lambda state: create_followup_node(state, llm=provider))
    workflow.add_node("final_response", final_response_node)

    # Add Edges
    workflow.add_edge(START, "load_context")
    workflow.add_edge("load_context", "understand_question")
    workflow.add_edge("understand_question", "create_plan")
    workflow.add_edge("create_plan", "select_tool")
    workflow.add_edge("select_tool", "execute_tool")
    workflow.add_edge("execute_tool", "inspect_result")

    # Conditional routing after tool execution
    workflow.add_conditional_edges(
        "inspect_result",
        should_continue_tool_execution,
        {
            "select_tool": "select_tool",
            "synthesize_finding": "synthesize_finding",
        },
    )

    workflow.add_edge("synthesize_finding", "validate_evidence")
    workflow.add_edge("validate_evidence", "create_followup")

    # Conditional routing after validation and followup
    workflow.add_conditional_edges(
        "create_followup",
        route_after_validation,
        {
            "select_tool": "select_tool",
            "synthesize_finding": "synthesize_finding",
            "final_response": "final_response",
        },
    )

    workflow.add_edge("final_response", END)

    return workflow


def run_analytical_agent(
    question: str,
    parquet_path: str,
    dataset_id: Optional[str] = None,
    llm: Optional[BaseLLMProvider] = None,
    max_iterations: int = 10,
) -> AgentState:
    """Convenience runner compiling and executing the analytical graph."""
    graph = build_analytical_graph(llm=llm).compile()
    initial_state = AgentState(
        question=question,
        parquet_path=parquet_path,
        dataset_id=dataset_id,
        max_iterations=max_iterations,
    )
    result_dict = graph.invoke(initial_state)
    if isinstance(result_dict, dict):
        return AgentState.model_validate(result_dict)
    return result_dict
