"""State definition for LangGraph Analytical Agent."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from packages.evidence.models import Evidence, Finding


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    status: str = "pending"  # "pending", "success", "error"
    error_message: Optional[str] = None


class AgentState(BaseModel):
    """The central state flowing through the LangGraph analytics execution."""
    question: str
    parquet_path: str
    dataset_id: Optional[str] = None

    # Context & Schema
    schema_info: Dict[str, str] = Field(default_factory=dict)
    sample_records: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_summary: str = ""

    # Planning & Intent
    intent_summary: str = ""
    target_columns: List[str] = Field(default_factory=list)
    plan_steps: List[str] = Field(default_factory=list)
    current_step_index: int = 0

    # Tool Execution & Evidence
    pending_tool_call: Optional[ToolCallRecord] = None
    executed_tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    evidence_ledger: List[Evidence] = Field(default_factory=list)

    # Findings & Synthesis
    synthesized_findings: List[Finding] = Field(default_factory=list)
    draft_answer: str = ""
    
    # Evidence Gate Verification
    validation_passed: bool = False
    validation_notes: List[str] = Field(default_factory=list)
    validation_attempts: int = 0

    # Final Output
    final_response: str = ""
    iteration_count: int = 0
    max_iterations: int = 12
    completed: bool = False
    errors: List[str] = Field(default_factory=list)
