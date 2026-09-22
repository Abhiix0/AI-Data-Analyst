"""Central orchestrator — runs the agent pipeline in order."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from packages.legacy.core.context import AnalysisContext
from packages.ingestion.csv_loader import load_csv
from packages.ingestion.excel_loader import load_excel
from packages.ingestion.kaggle_loader import load_kaggle
from packages.analytics.tools import generate_profile
from packages.legacy.agents.visualization_agent import run as run_visualization
from packages.legacy.agents.insight_agent import run as run_insights
from packages.legacy.agents.recommendation_agent import run as run_recommendations
from packages.legacy.agents.report_agent import run as run_report
import polars as pl


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
        pldf = load_kaggle(source.replace("kaggle:", "", 1))
        return pldf.to_pandas()
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Dataset file not found: {source}")
    ext = os.path.splitext(source)[1].lower()
    if ext == ".csv":
        return load_csv(source).to_pandas()
    if ext in (".xlsx", ".xls"):
        return load_excel(source).to_pandas()
    raise ValueError(f"Unsupported format '{ext}'. Use .csv, .xlsx, .xls, or kaggle:<ref>")


def run_pipeline(source: str, progress_callback=None, model: str = "llama-3.1-8b-instant") -> AnalysisContext:
    """Run the full analysis pipeline. Returns a populated AnalysisContext.

    Args:
        source: File path or kaggle:<ref>
        progress_callback: Optional callable(step: int, total: int, message: str)
                           Used by dashboard to update progress bar.
        model: Groq model name to use for LLM agents.
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
    ctx.profile = _safe_run(ctx, "Profiling", generate_profile, pl.from_pandas(df)) or {}

    _progress(2, "Generating visualizations...")
    ctx.chart_paths = _safe_run(ctx, "Visualization", run_visualization, df, ctx.profile) or []

    _progress(3, "Generating AI insights...")
    ctx.insights = _safe_run(ctx, "Insights", run_insights, ctx, model=model) or ["Analysis complete."]

    _progress(4, "Generating recommendations...")
    ctx.recommendations = _safe_run(ctx, "Recommendations", run_recommendations, ctx, model=model) or []

    _progress(5, "Writing report...")
    ctx.report_path = _safe_run(ctx, "Report", run_report, ctx)

    _progress(6, "Done!")
    return ctx
