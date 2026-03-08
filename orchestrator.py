"""Orchestrator — minimal Phase 1 pipeline.

This module implements the simple, function-based orchestration layer:

    dataset → data_cleaner → analyst → insight_agent → final result

The orchestrator is responsible for:
- loading the dataset
- calling the Phase 1 agents
- combining their structured outputs into a final analysis report
"""

from __future__ import annotations

from typing import Dict, Any
import os

import pandas as pd

from agents.data import data_cleaner, dataset_understanding_agent
from agents.analysis import (
    analyst,
    clustering_agent,
    anomaly_detection_agent,
    feature_importance_agent,
)
from agents.reasoning import insight_agent
from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle


def _load_dataset(source: str) -> pd.DataFrame:
    """Load a dataset from a local file or Kaggle reference."""
    # Kaggle dataset: format "kaggle:owner/dataset"
    if source.startswith("kaggle:"):
        dataset_ref = source.replace("kaggle:", "", 1)
        print(f"[Orchestrator] Loading Kaggle dataset: {dataset_ref}")
        return load_kaggle(dataset_ref)

    if not os.path.isfile(source):
        raise FileNotFoundError(f"Dataset file not found: {source}")

    ext = os.path.splitext(source)[1].lower()
    print(f"[Orchestrator] Loading local dataset: {source}")

    if ext == ".csv":
        return load_csv(source)
    if ext in (".xlsx", ".xls"):
        return load_excel(source)

    raise ValueError(
        f"Unsupported file format '{ext}'. Supported: .csv, .xlsx, .xls, or 'kaggle:<owner/dataset>'."
    )


def run_pipeline(source: str) -> Dict[str, Any]:
    """Run the analysis pipeline and return a structured report.

    The returned dictionary uses the same shape as individual agents:

    {
        "summary": ...,
        "metrics": {...},
        "insights": [...],
    }
    """
    print("=" * 60)
    print("  AI Data Analyst — Phase 1 Pipeline")
    print("=" * 60)
    print()

    # Step 1: Load data
    df = _load_dataset(source)
    print()

    # Derive a simple dataset name from the source for context.
    if source.startswith("kaggle:"):
        dataset_name = source.replace("kaggle:", "", 1)
    else:
        dataset_name = os.path.splitext(os.path.basename(source))[0]

    # Step 2: Dataset understanding
    dataset_context = dataset_understanding_agent.run(df, dataset_name)
    print("[Orchestrator] Dataset understanding complete.")
    print()

    # Step 3: Data cleaning analysis
    cleaning_result = data_cleaner.run(df)
    print("[Orchestrator] Data cleaning analysis complete.")
    print()

    # Step 4: Basic statistical analysis
    analysis_result = analyst.run(df)
    print("[Orchestrator] Basic statistical analysis complete.")
    print()

    # Step 5: Clustering analysis
    clustering_result = clustering_agent.run(df)
    print("[Orchestrator] Clustering analysis complete.")
    print()

    # Step 6: Anomaly detection
    anomaly_result = anomaly_detection_agent.run(df)
    print("[Orchestrator] Anomaly detection complete.")
    print()

    # Step 7: Feature importance analysis
    feature_result = feature_importance_agent.run(df, dataset_context)
    print("[Orchestrator] Feature importance analysis complete.")
    print()

    # Step 8: Insight generation (LLM-powered when available)
    insight_result = insight_agent.run(
        df,
        cleaning_result,
        analysis_result,
        dataset_context,
    )
    print("[Orchestrator] Insight generation complete.")
    print()

    # Combine into a final structured report
    combined_insights = (
        dataset_context["insights"]
        + cleaning_result["insights"]
        + analysis_result["insights"]
        + clustering_result["insights"]
        + anomaly_result["insights"]
        + feature_result["insights"]
        + insight_result["insights"]
    )

    combined_metrics: Dict[str, Any] = {
        "dataset_understanding": dataset_context["metrics"],
        "data_cleaning": cleaning_result["metrics"],
        "analysis": analysis_result["metrics"],
        "clustering": clustering_result["metrics"],
        "anomalies": anomaly_result["metrics"],
        "feature_importance": feature_result["metrics"],
        "insight_summary": insight_result["metrics"],
    }

    summary = (
        "Completed Phase 4 analysis: dataset understanding, basic data quality review, "
        "descriptive statistics, clustering, anomaly detection, feature importance, "
        "and high-level narrative insights."
    )

    final_report: Dict[str, Any] = {
        "summary": summary,
        "metrics": combined_metrics,
        "insights": combined_insights,
        "dataset_context": dataset_context,
    }

    return final_report

