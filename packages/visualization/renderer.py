"""Deterministic Plotly rendering engine transforming ChartSpec into interactive figures and HTML."""
from __future__ import annotations
import json
from typing import Any, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from packages.visualization.models import ChartSpec


def to_plotly_figure(spec: ChartSpec) -> go.Figure:
    """Render a ChartSpec into a Plotly Figure object."""
    df = pd.DataFrame(spec.data) if spec.data else pd.DataFrame()

    fig: Optional[go.Figure] = None

    if spec.chart_type == "bar":
        if spec.orientation == "h":
            fig = px.bar(df, x=spec.y, y=spec.x, color=spec.color, orientation="h", title=spec.title, barmode=spec.barmode or "relative")
        else:
            fig = px.bar(df, x=spec.x, y=spec.y, color=spec.color, title=spec.title, barmode=spec.barmode or "relative")

    elif spec.chart_type == "line":
        fig = px.line(df, x=spec.x, y=spec.y, color=spec.color, title=spec.title)

    elif spec.chart_type == "scatter":
        fig = px.scatter(df, x=spec.x, y=spec.y, color=spec.color, title=spec.title)

    elif spec.chart_type == "box":
        fig = px.box(df, x=spec.x, y=spec.y, color=spec.color, title=spec.title)

    elif spec.chart_type == "histogram":
        fig = px.histogram(df, x=spec.x, color=spec.color, title=spec.title)

    elif spec.chart_type == "pie":
        fig = px.pie(df, names=spec.x, values=spec.y if isinstance(spec.y, str) else None, title=spec.title)

    elif spec.chart_type == "heatmap":
        # Check if 2D matrix or records
        if "z" in spec.options:
            z_vals = spec.options["z"]
            x_labels = spec.options.get("x_labels", [])
            y_labels = spec.options.get("y_labels", [])
            fig = px.imshow(z_vals, x=x_labels, y=y_labels, title=spec.title, text_auto=True)
        elif not df.empty and spec.x and spec.y and "value" in df.columns:
            pivot = df.pivot(index=spec.y, columns=spec.x, values="value")
            fig = px.imshow(pivot, title=spec.title, text_auto=True)
        else:
            fig = go.Figure(layout=go.Layout(title=spec.title))
    else:
        fig = go.Figure(layout=go.Layout(title=spec.title))

    if fig is None:
        fig = go.Figure(layout=go.Layout(title=spec.title))

    # Apply aesthetic layout styling
    fig.update_layout(
        template="plotly_dark",
        title_font_size=16,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def to_json_spec(spec: ChartSpec) -> str:
    """Serialize ChartSpec to JSON."""
    return spec.model_dump_json(indent=2)


def to_html(spec: ChartSpec, include_plotlyjs: str = "cdn") -> str:
    """Render chart to standalone interactive HTML embedding."""
    fig = to_plotly_figure(spec)
    return fig.to_html(include_plotlyjs=include_plotlyjs, full_html=False)
