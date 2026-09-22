"""Automated Chart Selection Engine recommending charts based on data distributions and profile metrics."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import polars as pl

from packages.visualization.models import ChartSpec


def generate_chart_specs_from_df(df: pl.DataFrame, max_charts: int = 8) -> List[ChartSpec]:
    """Generate prioritized ChartSpec list directly from a Polars DataFrame."""
    if df.is_empty() or len(df.columns) == 0:
        return []

    charts: List[ChartSpec] = []
    
    # Identify numeric and categorical columns
    numeric_cols = [
        col for col, dtype in df.schema.items()
        if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64)
    ]
    cat_cols = [
        col for col, dtype in df.schema.items()
        if dtype in (pl.String, pl.Categorical)
    ]

    # 1. Bar charts for low-to-medium cardinality categorical columns
    for col in cat_cols[:4]:
        val_counts = df[col].drop_nulls().value_counts().sort("count", descending=True).head(15)
        if 2 <= len(val_counts) <= 25:
            records = [{"category": str(r[col]), "count": int(r["count"])} for r in val_counts.iter_rows(named=True)]
            charts.append(
                ChartSpec(
                    chart_type="bar",
                    title=f"Distribution of {col}",
                    x="category",
                    y="count",
                    data=records,
                )
            )

    # 2. Histograms / Boxplots for numeric columns
    for col in numeric_cols[:4]:
        sample_vals = df[col].drop_nulls().head(500).to_list()
        records = [{col: float(v)} for v in sample_vals]
        charts.append(
            ChartSpec(
                chart_type="histogram",
                title=f"Histogram of {col}",
                x=col,
                data=records,
            )
        )

    # 3. Correlation Heatmap if 2 or more numeric columns
    if len(numeric_cols) >= 2:
        sub_df = df.select(numeric_cols[:6]).drop_nulls()
        if len(sub_df) >= 5:
            corr_matrix = []
            cols_selected = numeric_cols[:6]
            for c1 in cols_selected:
                row = []
                for c2 in cols_selected:
                    if c1 == c2:
                        row.append(1.0)
                    else:
                        r = sub_df.select(pl.corr(c1, c2)).item()
                        row.append(round(float(r) if r is not None else 0.0, 3))
                corr_matrix.append(row)

            charts.append(
                ChartSpec(
                    chart_type="heatmap",
                    title="Correlation Heatmap",
                    options={
                        "z": corr_matrix,
                        "x_labels": cols_selected,
                        "y_labels": cols_selected,
                    },
                )
            )

    # 4. Scatter plot for first 2 numeric columns
    if len(numeric_cols) >= 2:
        col_x, col_y = numeric_cols[0], numeric_cols[1]
        sample_scatter = df.select([col_x, col_y]).drop_nulls().head(300)
        records = [{col_x: float(r[col_x]), col_y: float(r[col_y])} for r in sample_scatter.iter_rows(named=True)]
        charts.append(
            ChartSpec(
                chart_type="scatter",
                title=f"{col_x} vs {col_y}",
                x=col_x,
                y=col_y,
                data=records,
            )
        )

    return charts[:max_charts]


def generate_chart_specs_from_profile(profile: Dict[str, Any], df: Optional[pl.DataFrame] = None) -> List[Dict[str, Any]]:
    """Legacy backward-compatible bridge for orchestrator and legacy dashboard."""
    if df is not None:
        specs = generate_chart_specs_from_df(df)
        return [spec.model_dump() for spec in specs]

    # Heuristic from profile dictionary
    charts: List[Dict[str, Any]] = []
    numeric_stats = profile.get("numeric_stats", {})
    outliers = profile.get("outliers", {})
    top_correlations = profile.get("top_correlations", [])
    categorical_stats = profile.get("categorical_stats", {})

    for col in list(numeric_stats.keys())[:4]:
        charts.append({"type": "histogram", "col": col})

    for col in list(outliers.keys())[:3]:
        charts.append({"type": "box", "col": col})

    for pair in top_correlations[:3]:
        charts.append({"type": "scatter", "col_a": pair.get("col_a"), "col_b": pair.get("col_b"), "r": pair.get("r")})

    for col, stat in list(categorical_stats.items())[:4]:
        charts.append({"type": "bar", "col": col})

    return charts
