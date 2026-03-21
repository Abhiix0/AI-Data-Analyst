"""Central orchestrator — runs the agent pipeline in order."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from core.context import AnalysisContext
from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle
from agents.profiling_agent import run as run_profiling
from agents.visualization_agent import run as run_visualization
from agents.insight_agent import run as run_insights
from agents.recommendation_agent import run as run_recommendations
from agents.report_agent import run as run_report


def _validate_dataset(df: pd.DataFrame, source: str) -> None:
    """Raise ValueError for datasets that cannot be analyzed."""
    if df is None or df.empty:
        raise ValueError(f"Dataset is empty: {source}")
    if len(df.columns) < 2:
        raise ValueError(f"Dataset has only {len(df.columns)} column — need at least 2 to analyze.")
    if len(df) < 5:
        raise ValueError(f"Dataset has only {len(df)} rows — too small to analyze meaningfully.")


def _safe_run(ctx: AnalysisContext, step_name: str, fn, *args, **kwargs):
    """Run an agent safely. On failure, log the error to ctx and continue."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        error_msg = f"{step_name} failed: {str(e)}"
        ctx.errors.append(error_msg)
        print(f"[WARNING] {error_msg}")
        return None


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


def run_pipeline(source: str, progress_callback=None) -> AnalysisContext:
    """Run the full analysis pipeline. Returns a populated AnalysisContext.

    Args:
        source: File path or kaggle:<ref>
        progress_callback: Optional callable(step: int, total: int, message: str)
                           Used by dashboard to update progress bar.
    """
    def _progress(step, msg):
        if progress_callback:
            progress_callback(step, 6, msg)

    df = _load_dataset(source)
    file_name = (
        source.replace("kaggle:", "", 1)
        if source.startswith("kaggle:")
        else os.path.splitext(os.path.basename(source))[0]
    )

    _validate_dataset(df, source)

    ctx = AnalysisContext(df=df, file_name=file_name)

    _progress(1, "Profiling dataset...")
    ctx.profile = _safe_run(ctx, "Profiling", run_profiling, df) or {}

    _progress(2, "Generating visualizations...")
    ctx.chart_paths = _safe_run(ctx, "Visualization", run_visualization, df, ctx.profile) or []

    _progress(3, "Generating AI insights...")
    ctx.insights = _safe_run(ctx, "Insights", run_insights, ctx) or ["Analysis complete."]

    _progress(4, "Generating recommendations...")
    ctx.recommendations = _safe_run(ctx, "Recommendations", run_recommendations, ctx) or []

    _progress(5, "Writing report...")
    ctx.report_path = _safe_run(ctx, "Report", run_report, ctx)

    _progress(6, "Done!")
    return ctx
