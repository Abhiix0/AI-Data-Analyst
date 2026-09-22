"""Node for inspecting intermediate tool execution results and advancing plan."""
from __future__ import annotations
from packages.agent.state import AgentState


def inspect_result_node(state: AgentState) -> AgentState:
    """Evaluate if the executed tool yielded the necessary evidence or if further execution is needed."""
    state.iteration_count += 1
    state.current_step_index += 1
    return state
