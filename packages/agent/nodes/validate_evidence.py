"""Node for hard evidence verification gate ensuring all numbers in findings are grounded."""
from __future__ import annotations
import re
from typing import Any, List, Set
from packages.agent.state import AgentState


def _extract_numbers_from_text(text: str) -> List[float]:
    """Extract numeric tokens from narrative text."""
    # Match integers, floats, percentages, e.g., 42, 3.14, 85.5%, -0.75
    pattern = r"[-+]?\b\d+(?:\.\d+)?%?"
    matches = re.findall(pattern, text)
    numbers = []
    for m in matches:
        clean = m.rstrip("%")
        try:
            val = float(clean)
            # Skip trivial structural numbers like 1, 2, 3 or year-like 2024..2030 unless relevant
            if val in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0):
                continue
            numbers.append(val)
        except ValueError:
            continue
    return numbers


def _extract_numbers_from_evidence(data: Any, found_numbers: Set[float]) -> None:
    """Recursively harvest all numeric values from nested evidence objects/dictionaries/lists."""
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        found_numbers.add(round(float(data), 4))
    elif isinstance(data, dict):
        for v in data.values():
            _extract_numbers_from_evidence(v, found_numbers)
    elif isinstance(data, list):
        for item in data:
            _extract_numbers_from_evidence(item, found_numbers)
    elif isinstance(data, str):
        # Also check numbers inside stringified values
        for n in _extract_numbers_from_text(data):
            found_numbers.add(round(n, 4))


def _is_grounded(target: float, evidence_numbers: Set[float], tolerance: float = 0.02) -> bool:
    """Check if target number is close to any number in evidence within relative/absolute tolerance."""
    for ev_num in evidence_numbers:
        # Exact or close absolute match
        if abs(target - ev_num) < 0.05:
            return True
        # Relative match for larger numbers
        if ev_num != 0 and abs((target - ev_num) / ev_num) < tolerance:
            return True
        # Percentage match (e.g., target 85% vs 0.85)
        if abs(target - (ev_num * 100)) < 0.1 or abs((target / 100) - ev_num) < 0.001:
            return True
    return False


def validate_evidence_node(state: AgentState) -> AgentState:
    """Hard gate: Verifies all numbers in draft_answer and synthesized_findings exist in evidence ledger."""
    state.validation_attempts += 1
    state.validation_notes = []

    if not state.evidence_ledger:
        state.validation_passed = False
        state.validation_notes.append("Validation failed: No evidence in ledger.")
        return state

    # Harvest all numbers from evidence ledger
    ledger_numbers: Set[float] = set()
    for ev in state.evidence_ledger:
        _extract_numbers_from_evidence(ev.value, ledger_numbers)

    # Check narrative text
    all_text = state.draft_answer + " " + " ".join([f.description for f in state.synthesized_findings])
    text_numbers = _extract_numbers_from_text(all_text)

    unsubstantiated = []
    for num in text_numbers:
        if not _is_grounded(num, ledger_numbers):
            unsubstantiated.append(num)

    if unsubstantiated:
        state.validation_passed = False
        state.validation_notes.append(
            f"Unsubstantiated numbers detected in findings: {unsubstantiated[:5]}. Must be present in evidence ledger."
        )
    else:
        state.validation_passed = True
        state.validation_notes.append("Validation passed: All metrics verified against evidence ledger.")

    return state
