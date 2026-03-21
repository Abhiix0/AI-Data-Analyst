from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from agents.understanding_agent import run as run_understanding
from agents.profiling_agent import run as run_profiling
from agents.insight_agent import run as run_insights
from agents.recommendation_agent import run as run_recommendations
from agents.visualization_agent import run as run_visualization
from agents.report_agent import run as run_report
from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle


def _load_dataset(source: str) -> pd.DataFrame:
    if source.startswith("kaggle:"):
        return load_kaggle(source.replace("kaggle:", "", 1))
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Dataset file not found: {source}")
    ext = os.path.splitext(source)[1].lower()
    if ext == ".csv":
        return load_csv(source)
    if ext in (".xlsx", ".xls"):
        return load_excel(source)
    raise ValueError(f"Unsupported format '{ext}'. Use .csv, .xlsx, .xls, or kaggle:<ref>")


def run_pipeline(source: str) -> Dict[str, Any]:
    print("=" * 60)
    print("  AI Data Analyst")
    print("=" * 60)

    df = _load_dataset(source)
    dataset_name = (
        source.replace("kaggle:", "", 1)
        if source.startswith("kaggle:")
        else os.path.splitext(os.path.basename(source))[0]
    )

    print("[1/6] Understanding dataset...")
    context = run_understanding(df, dataset_name)

    print("[2/6] Profiling data...")
    profile = run_profiling(df)

    print("[3/6] Generating insights with Claude...")
    insight_result = run_insights(df, profile, context)

    print("[4/6] Generating recommendations with Claude...")
    rec_result = run_recommendations(insight_result["insights"], profile, context)

    print("[5/6] Generating visualizations...")
    viz_result = run_visualization(df, profile)

    print("[6/6] Writing report...")
    report_result = run_report(
        source=source,
        context=context,
        profile=profile,
        insights=insight_result["insights"],
        recommendations=rec_result["insights"],
        charts=viz_result["chart_paths"],
    )

    print("\nDone!")
    return {
        "summary": "Pipeline complete.",
        "metrics": {
            "data_cleaning": {
                "duplicate_rows": profile["metrics"]["duplicate_rows"],
                "missing": profile["metrics"]["missing"],
            },
            "outliers": profile["metrics"]["outliers"],
            "visualizations": viz_result["metrics"],
            "report": report_result["metrics"],
        },
        "insights": insight_result["insights"],
        "recommendations": rec_result["insights"],
        "dataset_context": context,
        "profile": profile,
        "report_path": report_result.get("report_path"),
        "chart_paths": viz_result.get("chart_paths", []),
    }
