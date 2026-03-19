from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""Orchestrator — full pipeline coordinating all agents."""

from typing import Dict, Any

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from agents.data import data_cleaner, dataset_understanding_agent
from agents.analysis import (
    analyst,
    clustering_agent,
    anomaly_detection_agent,
    feature_importance_agent,
    pattern_detection_agent,
    outlier_detection_agent,
)
from agents.reasoning import insight_agent, recommendation_agent
from agents.reporting import visualization_agent, report_agent
from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle


def _load_dataset(source: str) -> pd.DataFrame:
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
    raise ValueError(f"Unsupported format '{ext}'. Supported: .csv, .xlsx, .xls, kaggle:<ref>")


def run_pipeline(source: str) -> Dict[str, Any]:
    print("=" * 60)
    print("  AI Data Analyst — Full Pipeline")
    print("=" * 60)
    print()

    # Step 1: Load
    df = _load_dataset(source)
    print()

    dataset_name = (
        source.replace("kaggle:", "", 1)
        if source.startswith("kaggle:")
        else os.path.splitext(os.path.basename(source))[0]
    )

    # Step 2: Dataset understanding
    dataset_context = dataset_understanding_agent.run(df, dataset_name)
    print("[Orchestrator] Dataset understanding complete.\n")

    # Step 3: Data cleaning
    cleaning_result = data_cleaner.run(df)
    print("[Orchestrator] Data cleaning complete.\n")

    # Step 4: Statistical analysis
    analysis_result = analyst.run(df)
    print("[Orchestrator] Statistical analysis complete.\n")

    # Step 5: Pattern detection
    pattern_result = pattern_detection_agent.run(df)
    print("[Orchestrator] Pattern detection complete.\n")

    # Step 6: Outlier detection
    outlier_result = outlier_detection_agent.run(df)
    print("[Orchestrator] Outlier detection complete.\n")

    # Step 7: Clustering
    clustering_result = clustering_agent.run(df)
    print("[Orchestrator] Clustering complete.\n")

    # Step 8: Anomaly detection
    anomaly_result = anomaly_detection_agent.run(df)
    print("[Orchestrator] Anomaly detection complete.\n")

    # Step 9: Feature importance
    feature_result = feature_importance_agent.run(df, dataset_context)
    print("[Orchestrator] Feature importance complete.\n")

    # Step 10: Insights (LLM-powered)
    insight_result = insight_agent.run(df, cleaning_result, analysis_result, dataset_context)
    print("[Orchestrator] Insight generation complete.\n")

    # Build profile dict for agents that need the old-style profile shape
    profile = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "missing_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_stats": df.select_dtypes(include="number").describe().to_dict(),
        "categorical_summary": {
            col: {
                "unique_values": int(df[col].nunique()),
                "top_values": df[col].value_counts().head(5).to_dict(),
            }
            for col in df.select_dtypes(include=["object", "category"]).columns
        },
    }

    all_insights_so_far = (
        dataset_context["insights"]
        + cleaning_result["insights"]
        + analysis_result["insights"]
        + pattern_result["insights"]
        + outlier_result["insights"]
        + clustering_result["insights"]
        + anomaly_result["insights"]
        + feature_result["insights"]
        + insight_result["insights"]
    )

    # Step 11: Recommendations (LLM-powered)
    recommendation_result = recommendation_agent.run(
        profile,
        pattern_result["metrics"],
        outlier_result["metrics"].get("outlier_report", {}),
        all_insights_so_far,
    )
    print("[Orchestrator] Recommendations complete.\n")

    # Step 12: Visualizations
    viz_result = visualization_agent.run(df)
    print("[Orchestrator] Visualizations complete.\n")

    # Step 13: Report
    report_result = report_agent.run(
        source=source,
        profile=profile,
        charts=viz_result["chart_paths"],
        patterns=pattern_result["metrics"],
        outliers=outlier_result["metrics"].get("outlier_report", {}),
        insights=all_insights_so_far,
        recommendations=recommendation_result["insights"],
    )
    print("[Orchestrator] Report generation complete.\n")

    # Combine everything
    combined_insights = all_insights_so_far + recommendation_result["insights"]

    combined_metrics: Dict[str, Any] = {
        "dataset_understanding": dataset_context["metrics"],
        "data_cleaning": cleaning_result["metrics"],
        "analysis": analysis_result["metrics"],
        "patterns": pattern_result["metrics"],
        "outliers": outlier_result["metrics"],
        "clustering": clustering_result["metrics"],
        "anomalies": anomaly_result["metrics"],
        "feature_importance": feature_result["metrics"],
        "insight_summary": insight_result["metrics"],
        "recommendations": recommendation_result["metrics"],
        "visualizations": viz_result["metrics"],
        "report": report_result["metrics"],
    }

    return {
        "summary": "Full pipeline complete: 13 steps, all agents executed.",
        "metrics": combined_metrics,
        "insights": combined_insights,
        "dataset_context": dataset_context,
        "report_path": report_result.get("report_path"),
        "chart_paths": viz_result.get("chart_paths", []),
    }

