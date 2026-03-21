"""Visualization Agent — returns chart metadata for the dashboard to render."""
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd


def run(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Determine which charts are worth rendering based on the profile.

    Returns a list of chart metadata dicts (column names, chart type, etc.)
    that the dashboard uses to generate interactive Plotly charts.
    No files are written — all rendering happens in the dashboard.
    """
    if df.empty or len(df.columns) == 0:
        return []

    charts: List[Dict[str, Any]] = []

    numeric_stats = profile.get("numeric_stats", {})
    outliers = profile.get("outliers", {})
    top_correlations = profile.get("top_correlations", [])
    categorical_stats = profile.get("categorical_stats", {})

    numeric_cols = list(numeric_stats.keys())
    cat_cols = list(categorical_stats.keys())

    # Histograms — prioritize skewed or outlier-prone columns
    priority_numeric = sorted(
        numeric_cols,
        key=lambda c: (c in outliers, abs(numeric_stats[c].get("skew", 0))),
        reverse=True,
    )
    for col in priority_numeric[:6]:
        charts.append({"type": "histogram", "col": col})

    # Box plots — only for columns with outliers
    for col in list(outliers.keys())[:4]:
        charts.append({"type": "box", "col": col})

    # Scatter plots — top correlated pairs
    strong_pairs = [c for c in top_correlations if abs(c["r"]) >= 0.5][:3]
    for pair in strong_pairs:
        charts.append({"type": "scatter", "col_a": pair["col_a"], "col_b": pair["col_b"], "r": pair["r"]})

    # Correlation heatmap
    if len(numeric_cols) >= 2:
        charts.append({"type": "heatmap", "cols": numeric_cols})

    # Bar charts — categorical columns with 2-20 unique values
    useful_cat = [c for c in cat_cols if 2 <= categorical_stats[c]["unique_count"] <= 20][:4]
    for col in useful_cat:
        charts.append({"type": "bar", "col": col})

    return charts
