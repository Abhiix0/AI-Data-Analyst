"""Node for formatting final agent response with verified evidence citations."""
from __future__ import annotations
from packages.agent.state import AgentState


def final_response_node(state: AgentState) -> AgentState:
    """Format final response, appending evidence references and completion flag."""
    findings_bullets = "\n".join([
        f"- **{f.title}** ({f.category.capitalize()}, {f.strength.capitalize()}): {f.description}"
        for f in state.synthesized_findings
    ])

    citations = "\n".join([
        f"- `[Evidence {i+1}]` **{ev.metric_name}**: `{ev.source_query}`"
        for i, ev in enumerate(state.evidence_ledger)
    ])

    disclaimer = ""
    if not state.validation_passed:
        disclaimer = "\n> [!WARNING]\n> *Some metrics could not be fully reconciled with raw deterministic tool outputs.*\n\n"

    response_text = (
        f"{disclaimer}"
        f"### Summary\n{state.draft_answer}\n\n"
        f"### Key Findings\n{findings_bullets or 'No structured findings generated.'}\n\n"
        f"### Evidence Ledger ({len(state.evidence_ledger)} items)\n{citations or 'None'}"
    )

    state.final_response = response_text
    state.completed = True
    return state
