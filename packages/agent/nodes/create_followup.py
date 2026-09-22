"""Node for creating follow-up investigation queries and deep-dive steps."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

from packages.agent.state import AgentState
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class FollowupCreationSchema(BaseModel):
    should_investigate: bool = Field(..., description="Whether a deeper follow-up investigation is warranted")
    followup_steps: List[str] = Field(default_factory=list, description="Targeted follow-up analytical steps")
    rationale: str = Field("", description="Reason for following up or stopping")


def create_followup_node(state: AgentState, llm: Optional[BaseLLMProvider] = None, max_followup_depth: int = 2) -> AgentState:
    """Evaluate findings and determine if deeper drilling / follow-up investigation is warranted."""
    # Enforce maximum depth
    if state.iteration_count >= state.max_iterations or state.current_step_index >= 6:
        return state

    if not state.synthesized_findings:
        return state

    if llm is not None:
        try:
            findings_text = "\n".join([f"- {f.title}: {f.description}" for f in state.synthesized_findings])
            prompt = (
                f"You are an Elite Data Scientist reviewing intermediate findings.\n"
                f"Question: {state.question}\n"
                f"Current Findings:\n{findings_text}\n"
                f"Schema: {state.schema_info}\n\n"
                "Should we dive deeper into any specific sub-segment, driver, or anomaly? "
                "Only recommend follow-ups if there is a compelling, high-value unanswered question."
            )
            result = llm.generate_structured(
                messages=[LLMMessage(role="user", content=prompt)],
                schema=FollowupCreationSchema,
            )
            if result.should_investigate and result.followup_steps:
                # Append new steps to plan
                for step in result.followup_steps:
                    if step not in state.plan_steps:
                        state.plan_steps.append(step)
                return state
        except Exception:
            pass

    # Heuristic follow-up: if strong segment difference found, drill into top subset
    return state
