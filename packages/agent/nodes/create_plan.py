"""Node for creating an analytical investigation plan."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from packages.agent.state import AgentState
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class PlanCreationSchema(BaseModel):
    steps: List[str] = Field(..., description="1 to 4 ordered analytical steps to answer the question")


def create_plan_node(state: AgentState, llm: Optional[BaseLLMProvider] = None) -> AgentState:
    """Generate a step-by-step plan for answering the question using deterministic tools."""
    if state.plan_steps:
        return state

    if llm and not hasattr(llm, "canned_responses"):
        try:
            prompt = (
                f"You are a Senior Data Analyst planning an investigation.\n"
                f"Question: {state.question}\n"
                f"Intent: {state.intent_summary}\n"
                f"Target Columns: {', '.join(state.target_columns)}\n"
                f"Available Tools: inspect_schema, describe_column, calculate_missingness, calculate_correlation, "
                f"detect_outliers, filter_dataset, group_by, aggregate, compare_segments, find_trends, find_anomalies, "
                f"test_hypothesis, run_sql.\n\n"
                "Create a concise list of 1 to 3 analytical steps to gather the necessary evidence."
            )
            result = llm.generate_structured(
                messages=[LLMMessage(role="user", content=prompt)],
                schema=PlanCreationSchema,
            )
            if result.steps:
                state.plan_steps = result.steps
                state.current_step_index = 0
                return state
        except Exception:
            pass

    # Heuristic fallback planning
    cols = state.target_columns
    q_lower = state.question.lower()
    steps = []

    if any(w in q_lower for w in ["churn", "compare", "segment", "difference", "by"]):
        if len(cols) >= 2:
            steps.append(f"Compare segments of '{cols[1]}' across '{cols[0]}'")
        else:
            steps.append(f"Group and aggregate '{cols[0]}'")
    elif any(w in q_lower for w in ["correlat", "relation", "impact"]):
        steps.append("Calculate correlation matrix")
    elif any(w in q_lower for w in ["outlier", "anomaly", "unusual"]):
        if cols:
            steps.append(f"Detect outliers in '{cols[0]}'")
    elif any(w in q_lower for w in ["trend", "time", "over"]):
        if len(cols) >= 2:
            steps.append(f"Find trends of '{cols[1]}' over '{cols[0]}'")
        elif cols:
            steps.append(f"Find trends of '{cols[0]}'")
    else:
        if cols:
            steps.append(f"Calculate distribution metrics for '{cols[0]}'")
        else:
            steps.append("Calculate missingness and summary statistics")

    state.plan_steps = steps or ["Analyze relevant column distributions"]
    state.current_step_index = 0
    return state
