"""Evaluation Benchmark Runner executing test cases against the LangGraph analytical agent."""
from __future__ import annotations
import glob
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import polars as pl
import yaml

from packages.agent.graph import run_analytical_agent
from tests.evaluation.models import EvalCase, EvalResult, BenchmarkSummary


def _create_synthetic_datasets(base_dir: str) -> Dict[str, str]:
    """Generate synthetic Parquet datasets for evaluation cases."""
    os.makedirs(base_dir, exist_ok=True)
    paths = {}

    # 1. Sales Dataset
    sales_df = pl.DataFrame({
        "order_id": list(range(1, 101)),
        "region": ["North"] * 50 + ["South"] * 50,
        "price": [10.0 + i * 2 for i in range(100)],
        "units": [100 - i for i in range(100)],
        "revenue": [(10.0 + i * 2) * (100 - i) for i in range(100)],
        "satisfaction": [4.2] * 50 + [3.8] * 50,
    })
    sales_path = os.path.join(base_dir, "eval_sales.parquet")
    sales_df.write_parquet(sales_path)
    paths["sales"] = sales_path

    # 2. Churn Dataset
    churn_df = pl.DataFrame({
        "customer_id": list(range(1, 101)),
        "contract": ["Month-to-month"] * 50 + ["Two-year"] * 50,
        "churn": ["Yes"] * 35 + ["No"] * 65,
        "charges": [70.0 + i * 0.5 for i in range(100)],
    })
    churn_path = os.path.join(base_dir, "eval_churn.parquet")
    churn_df.write_parquet(churn_path)
    paths["churn"] = churn_path

    # 3. Employees Dataset
    emp_df = pl.DataFrame({
        "employee_id": list(range(1, 101)),
        "department": ["Engineering"] * 60 + ["Sales"] * 40,
        "salary": [80000.0 + i * 1000 for i in range(98)] + [450000.0, 500000.0],
        "bonus": [5000.0 + i * 200 for i in range(100)],
    })
    emp_path = os.path.join(base_dir, "eval_employees.parquet")
    emp_df.write_parquet(emp_path)
    paths["employees"] = emp_path

    return paths


def load_all_eval_cases(cases_dir: Optional[str] = None) -> List[EvalCase]:
    """Load all evaluation cases from YAML files."""
    if not cases_dir:
        cases_dir = os.path.join(os.path.dirname(__file__), "cases")

    case_files = glob.glob(os.path.join(cases_dir, "*.yaml")) + glob.glob(os.path.join(cases_dir, "*.yml"))
    all_cases: List[EvalCase] = []

    for fpath in case_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "cases" in data:
                for c in data["cases"]:
                    all_cases.append(EvalCase.model_validate(c))

    return all_cases


def run_benchmark(cases: Optional[List[EvalCase]] = None) -> BenchmarkSummary:
    """Run full evaluation suite and return aggregate benchmark metrics."""
    eval_cases = cases or load_all_eval_cases()
    if not eval_cases:
        return BenchmarkSummary(
            total_cases=0,
            passed_cases=0,
            pass_rate=0.0,
            tool_precision=0.0,
            evidence_pass_rate=0.0,
            avg_latency_s=0.0,
            results=[],
        )

    temp_dir = tempfile.mkdtemp()
    try:
        dataset_paths = _create_synthetic_datasets(temp_dir)
        results: List[EvalResult] = []

        for case in eval_cases:
            parquet_path = dataset_paths.get(case.dataset_type, dataset_paths["sales"])
            start_time = time.time()
            err_msg = None
            tool_sel = None
            tool_matched = False
            ev_count = 0
            val_passed = False
            findings_count = 0

            try:
                state = run_analytical_agent(
                    question=case.question,
                    parquet_path=parquet_path,
                )
                executed_tools = [t.tool_name for t in state.executed_tool_calls]
                tool_sel = executed_tools[0] if executed_tools else None
                tool_matched = any(
                    any(t == exp or exp in str(t) for exp in case.expected_tools)
                    for t in executed_tools
                ) if case.expected_tools and executed_tools else True
                ev_count = len(state.evidence_ledger)
                val_passed = state.validation_passed
                findings_count = len(state.synthesized_findings)
            except Exception as e:
                err_msg = str(e)

            latency = time.time() - start_time
            passed = (
                err_msg is None
                and val_passed
                and ev_count >= 1
                and (tool_matched or findings_count >= 1)
            )

            results.append(
                EvalResult(
                    case_id=case.id,
                    passed=passed,
                    tool_selected=tool_sel,
                    tool_matched=tool_matched,
                    evidence_count=ev_count,
                    validation_passed=val_passed,
                    synthesized_findings_count=findings_count,
                    latency_s=latency,
                    error=err_msg,
                )
            )

        passed_cases = sum(1 for r in results if r.passed)
        tool_matches = sum(1 for r in results if r.tool_matched)
        ev_passes = sum(1 for r in results if r.validation_passed)
        total = len(results)

        return BenchmarkSummary(
            total_cases=total,
            passed_cases=passed_cases,
            pass_rate=passed_cases / total if total > 0 else 0.0,
            tool_precision=tool_matches / total if total > 0 else 0.0,
            evidence_pass_rate=ev_passes / total if total > 0 else 0.0,
            avg_latency_s=sum(r.latency_s for r in results) / total if total > 0 else 0.0,
            results=results,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Running Evaluation Benchmark Suite...")
    summary = run_benchmark()
    print("\n" + "=" * 60)
    print(f"Total Cases:         {summary.total_cases}")
    print(f"Passed Cases:        {summary.passed_cases} ({summary.pass_rate:.1%})")
    print(f"Tool Match Rate:     {summary.tool_precision:.1%}")
    print(f"Evidence Gate Pass:  {summary.evidence_pass_rate:.1%}")
    print(f"Avg Latency:         {summary.avg_latency_s:.2f}s")
    print("=" * 60)
    for r in summary.results:
        status_icon = "[PASS]" if r.passed else "[FAIL]"
        print(f"{status_icon} Case: {r.case_id:<30} | Tool: {str(r.tool_selected):<20} | Ev: {r.evidence_count} | {r.latency_s:.2f}s")
