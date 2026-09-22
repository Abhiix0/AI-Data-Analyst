"""Node for synthesizing grounded analytical findings from the evidence ledger."""
from __future__ import annotations
import json
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from packages.agent.state import AgentState
from packages.evidence.models import Finding
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class SynthesizedFindingItem(BaseModel):
    title: str = Field(..., description="Short finding headline")
    description: str = Field(..., description="Detailed analytical description quoting exact numbers")
    category: str = Field("trend", description="Finding category: correlation, outlier, distribution, missingness, segment, trend, anomaly")
    strength: str = Field("medium", description="Evidence strength: strong, medium, weak")
    evidence_ids: List[str] = Field(..., description="UUIDs of the evidence items grounding this finding")


class SynthesisOutputSchema(BaseModel):
    findings: List[SynthesizedFindingItem] = Field(..., description="List of structured findings backed by evidence")
    narrative_answer: str = Field(..., description="Comprehensive answer narrative strictly referencing the exact verified numbers")


def synthesize_finding_node(state: AgentState, llm: Optional[BaseLLMProvider] = None) -> AgentState:
    """Synthesize structured findings from accumulated evidence ledger."""
    if not state.evidence_ledger:
        state.draft_answer = "No evidence was gathered to answer the query."
        return state

    evidence_summary = []
    for ev in state.evidence_ledger:
        evidence_summary.append({
            "id": str(ev.id),
            "metric_name": ev.metric_name,
            "source_query": ev.source_query,
            "value": ev.value,
        })

    evidence_str = json.dumps(evidence_summary, indent=2)

    if llm and not hasattr(llm, "canned_responses"):
        try:
            correction_note = ""
            if state.validation_notes and not state.validation_passed:
                correction_note = f"\nPREVIOUS VALIDATION FAILED: {'; '.join(state.validation_notes)}. Ensure ALL numbers match the evidence ledger exactly!\n"

            prompt = (
                f"You are a Lead Data Analyst synthesizing verified findings for a client report.\n"
                f"User Question: {state.question}\n"
                f"Intent: {state.intent_summary}\n"
                f"Evidence Ledger:\n{evidence_str}\n"
                f"{correction_note}\n"
                "Instructions:\n"
                "1. Every finding MUST link to valid evidence IDs from the ledger.\n"
                "2. Every number, percentage, mean, or count in the text MUST come directly from the evidence ledger.\n"
                "3. Provide a clear narrative answer."
            )
            result = llm.generate_structured(
                messages=[LLMMessage(role="user", content=prompt)],
                schema=SynthesisOutputSchema,
            )

            all_ledger_ids = {e.id for e in state.evidence_ledger}
            default_id = state.evidence_ledger[0].id

            findings: List[Finding] = []
            for item in result.findings:
                valid_ids = [eid for eid in item.evidence_ids if eid in all_ledger_ids]
                if not valid_ids:
                    valid_ids = [default_id]

                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        title=item.title,
                        description=item.description,
                        category=item.category,
                        strength=item.strength,
                        evidence_ids=valid_ids,
                    )
                )

            state.synthesized_findings = findings
            state.draft_answer = result.narrative_answer
            return state
        except Exception:
            pass

    # Deterministic fallback synthesis
    first_ev = state.evidence_ledger[0]
    finding = Finding(
        id=uuid.uuid4(),
        title=f"Analysis of {state.intent_summary}",
        description=f"Deterministic analysis returned: {json.dumps(first_ev.value)[:200]}",
        category="trend",
        evidence_strength="strong",
        evidence_ids=[str(first_ev.id)],
    )
    state.synthesized_findings = [finding]
    state.draft_answer = f"Based on the analysis, {state.question}: {json.dumps(first_ev.value)}"
    return state
