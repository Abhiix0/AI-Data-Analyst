"""Node for extracting analytical intent and target columns from user question."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from packages.agent.state import AgentState
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class QuestionUnderstandingSchema(BaseModel):
    intent_summary: str = Field(..., description="Concise analytical objective of the question")
    target_columns: List[str] = Field(..., description="Relevant column names from the dataset schema")


def understand_question_node(state: AgentState, llm: Optional[BaseLLMProvider] = None) -> AgentState:
    """Analyze the question in context of the schema and identify relevant columns."""
    if state.intent_summary and state.target_columns:
        return state

    schema_str = ", ".join([f"{col} ({dtype})" for col, dtype in state.schema_info.items()])
    
    if llm and not hasattr(llm, "canned_responses"):
        try:
            history_str = ""
            if state.conversation_history:
                recent = state.conversation_history[-4:]
                history_str = "\nRecent Conversation:\n" + "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in recent]) + "\n"

            prompt = (
                f"You are a Senior Data Analyst. Analyze this user query against the dataset schema:\n{history_str}\n"
                f"User Query: {state.question}\n"
                f"Dataset Schema: {schema_str}\n\n"
                "Identify the analytical intent and the exact relevant columns from the schema."
            )
            result = llm.generate_structured(
                messages=[LLMMessage(role="user", content=prompt)],
                schema=QuestionUnderstandingSchema,
            )
            state.intent_summary = result.intent_summary
            valid_cols = [c for c in result.target_columns if c in state.schema_info]
            state.target_columns = valid_cols or list(state.schema_info.keys())[:3]
            return state
        except Exception:
            pass

    # Heuristic fallback matching column names in question
    q_lower = state.question.lower()
    matched_cols = [col for col in state.schema_info.keys() if col.lower() in q_lower]
    if not matched_cols:
        matched_cols = list(state.schema_info.keys())[:3]

    state.intent_summary = f"Analyze '{state.question}' using columns: {', '.join(matched_cols)}"
    state.target_columns = matched_cols
    return state
