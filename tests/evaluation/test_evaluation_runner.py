"""Pytest suite for Evaluation Benchmark Suite (Phase 17)."""
import pytest
from tests.evaluation.runner import load_all_eval_cases, run_benchmark


def test_load_evaluation_cases():
    cases = load_all_eval_cases()
    assert len(cases) >= 5
    for c in cases:
        assert c.id is not None
        assert len(c.question) > 5


def test_evaluation_benchmark_pass_rate():
    summary = run_benchmark()
    assert summary.total_cases >= 5
    # Target >= 80% pass rate
    assert summary.pass_rate >= 0.80
    assert summary.evidence_pass_rate >= 0.80
    assert summary.tool_precision >= 0.80
