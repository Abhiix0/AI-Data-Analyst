"""AI Data Analyst — Streamlit Dashboard."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
load_dotenv()

from orchestrator import run_pipeline
from core.context import AnalysisContext

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2d2f3e;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1a1d27;
        border: 1px solid #2d2f3e;
        border-radius: 10px;
        padding: 16px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d27;
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8b8fa8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d2f3e !important;
        color: #ffffff !important;
    }

    /* Insight cards */
    .insight-card {
        background-color: #1a1d27;
        border-left: 4px solid #4f8ef7;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #e0e0e0;
    }

    /* Recommendation cards */
    .rec-card-info {
        background-color: #1a1d27;
        border-left: 4px solid #4f8ef7;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e0e0e0;
    }
    .rec-card-warning {
        background-color: #1f1a10;
        border-left: 4px solid #f7a94f;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e0e0e0;
    }
    .rec-card-critical {
        background-color: #1f1015;
        border-left: 4px solid #f74f4f;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e0e0e0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #8b8fa8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 16px;
        margin-top: 8px;
    }

    /* Divider */
    hr { border-color: #2d2f3e; }

    /* Dataframes */
    [data-testid="stDataFrame"] { border-radius: 8px; }

    /* Hide default Streamlit footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────
if "ctx" not in st.session_state:
    st.session_state.ctx = None

# ── Helpers ──────────────────────────────────────────────────────
def save_upload(uploaded_file) -> str:
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def _rec_severity(rec: str) -> str:
    """Classify recommendation severity by keywords."""
    rec_lower = rec.lower()
    critical_kws = ["drop", "remove", "critical", "severe", "corrupt", "invalid"]
    warning_kws = ["missing", "outlier", "imbalance", "skew", "duplicate", "impute"]
    if any(k in rec_lower for k in critical_kws):
        return "critical"
    if any(k in rec_lower for k in warning_kws):
        return "warning"
    return "info"


def _make_plotly_histogram(df: pd.DataFrame, col: str):
    fig = px.histogram(
        df, x=col, nbins=40,
        title=f"Distribution: {col}",
        color_discrete_sequence=["#4f8ef7"],
    )
    fig.update_layout(
        paper_bgcolor="#1a1d27", plot_bgcolor="#1a1d27",
        font_color="#e0e0e0", title_font_size=14,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def _make_plotly_box(df: pd.DataFrame, col: str):
    fig = px.box(
        df, y=col, title=f"Outliers: {col}",
        color_discrete_sequence=["#50c878"],
    )
    fig.update_layout(
        paper_bgcolor="#1a1d27", plot_bgcolor="#1a1d27",
        font_color="#e0e0e0", title_font_size=14,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def _make_plotly_scatter(df: pd.DataFrame, col_a: str, col_b: str, r: float):
    fig = px.scatter(
        df, x=col_a, y=col_b,
        title=f"{col_a} vs {col_b} (r={r})",
        opacity=0.5,
        color_discrete_sequence=["#f74f9a"],
    )
    fig.update_layout(
        paper_bgcolor="#1a1d27", plot_bgcolor="#1a1d27",
        font_color="#e0e0e0", title_font_size=14,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def _make_plotly_heatmap(df: pd.DataFrame, numeric_cols: list):
    corr = df[numeric_cols].corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.columns.tolist(),
        colorscale="RdBu",
        zmid=0,
        text=corr.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10},
    ))
    fig.update_layout(
        title="Correlation Heatmap",
        paper_bgcolor="#1a1d27", plot_bgcolor="#1a1d27",
        font_color="#e0e0e0", title_font_size=14,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def _make_plotly_bar(df: pd.DataFrame, col: str):
    counts = df[col].value_counts().head(15)
    fig = px.bar(
        x=counts.index.astype(str), y=counts.values,
        title=f"Value Counts: {col}",
        color_discrete_sequence=["#f7a94f"],
        labels={"x": col, "y": "Count"},
    )
    fig.update_layout(
        paper_bgcolor="#1a1d27", plot_bgcolor="#1a1d27",
        font_color="#e0e0e0", title_font_size=14,
        margin=dict(t=40, b=20, l=20, r=20),
        xaxis_tickangle=-30,
    )
    return fig


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 AI Data Analyst")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("Upload a CSV or Excel dataset to get AI-powered insights, charts, and a full report.")
    st.markdown("<hr>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"], label_visibility="collapsed")

    if uploaded:
        st.success(f"✅ **{uploaded.name}**")
        st.caption(f"{uploaded.size / 1024:.1f} KB")
        st.markdown("")

        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            path = save_upload(uploaded)
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(step: int, total: int, message: str):
                progress_bar.progress(step / total)
                status_text.caption(f"⚙️ {message}")

            try:
                ctx = run_pipeline(path, progress_callback=update_progress)
                st.session_state.ctx = ctx
                progress_bar.progress(1.0)
                status_text.caption("✅ Analysis complete!")
                st.success(f"✅ {len(ctx.insights)} insights generated!")
                if ctx.errors:
                    st.markdown("<hr>", unsafe_allow_html=True)
                    with st.expander("⚠️ Pipeline Warnings"):
                        for err in ctx.errors:
                            st.caption(f"• {err}")
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ {e}")
    else:
        st.info("👆 Upload a file to get started.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Powered by Groq · llama-3.1-8b-instant")

# ── Empty state ──────────────────────────────────────────────────
if st.session_state.ctx is None:
    st.markdown("# AI Data Analyst")
    st.markdown("#### Drop any dataset. Get a complete AI-powered analysis in seconds.")
    st.markdown("")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("**📋 Overview**\nDataset structure, shape, and preview")
    c2.markdown("**🔍 Data Quality**\nMissing values, duplicates, outliers")
    c3.markdown("**💡 AI Insights**\nLLM-generated findings from your data")
    c4.markdown("**📈 Charts**\nInteractive visualizations auto-generated")
    st.stop()

# ── Main dashboard ───────────────────────────────────────────────
ctx: AnalysisContext = st.session_state.ctx
df = ctx.df
profile = ctx.profile
numeric_cols = list(profile.get("numeric_stats", {}).keys())
cat_cols = list(profile.get("categorical_stats", {}).keys())

st.markdown(f"### 📊 {ctx.file_name}")
st.caption(ctx.shape_summary())

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Overview",
    "🔍 Data Quality",
    "💡 Insights",
    "📈 Charts",
    "📄 Report",
])

# ── Tab 1: Overview ──────────────────────────────────────────────
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    shape = profile["shape"]
    c1.metric("Rows", f"{shape['rows']:,}")
    c2.metric("Columns", shape["columns"])
    c3.metric("Insights", len(ctx.insights))
    c4.metric("Recommendations", len(ctx.recommendations))

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">Data Preview</p>', unsafe_allow_html=True)
    st.dataframe(df.head(20), use_container_width=True, height=350)

    st.markdown('<p class="section-header">Column Summary</p>', unsafe_allow_html=True)
    missing = profile.get("missing", {})
    outliers_prof = profile.get("outliers", {})
    col_rows = []
    for col, dtype in profile["dtypes"].items():
        miss_info = missing.get(col, {})
        out_info = outliers_prof.get(col, {})
        col_rows.append({
            "Column": col,
            "Type": dtype,
            "Missing": f"{miss_info.get('count', 0):,} ({miss_info.get('pct', 0)}%)" if miss_info else "—",
            "Outliers": f"{out_info.get('count', 0):,} ({out_info.get('pct', 0)}%)" if out_info else "—",
            "Unique": df[col].nunique(),
        })
    st.dataframe(pd.DataFrame(col_rows), use_container_width=True)

    if numeric_cols:
        st.markdown('<p class="section-header">Numeric Statistics</p>', unsafe_allow_html=True)
        stats_rows = []
        for col, stats in profile["numeric_stats"].items():
            stats_rows.append({
                "Column": col,
                "Mean": stats["mean"],
                "Median": stats["median"],
                "Std": stats["std"],
                "Min": stats["min"],
                "Max": stats["max"],
                "Skew": stats["skew"],
            })
        st.dataframe(pd.DataFrame(stats_rows), use_container_width=True)

# ── Tab 2: Data Quality ──────────────────────────────────────────
with tab2:
    miss_count = len(profile.get("missing", {}))
    dup_count = profile.get("duplicate_rows", 0)
    out_count = len(profile.get("outliers", {}))

    c1, c2, c3 = st.columns(3)
    c1.metric("Missing Columns", miss_count, delta=f"-{miss_count}" if miss_count else None, delta_color="inverse")
    c2.metric("Duplicate Rows", f"{dup_count:,}", delta=f"-{dup_count}" if dup_count else None, delta_color="inverse")
    c3.metric("Outlier Columns", out_count, delta=f"-{out_count}" if out_count else None, delta_color="inverse")

    st.markdown("<hr>", unsafe_allow_html=True)

    if missing:
        st.markdown('<p class="section-header">Missing Values</p>', unsafe_allow_html=True)
        miss_df = pd.DataFrame([
            {"Column": col, "Missing Count": info["count"], "Missing %": f"{info['pct']}%"}
            for col, info in missing.items()
        ])
        st.dataframe(miss_df, use_container_width=True)
    else:
        st.success("✅ No missing values — dataset is complete.")

    if dup_count > 0:
        st.warning(f"⚠️ **{dup_count:,} duplicate rows** detected.")
    else:
        st.success("✅ No duplicate rows.")

    outliers_data = profile.get("outliers", {})
    if outliers_data:
        st.markdown('<p class="section-header">Outliers (IQR Method)</p>', unsafe_allow_html=True)
        out_df = pd.DataFrame([
            {
                "Column": col,
                "Count": info["count"],
                "%": f"{info['pct']}%",
                "Lower Bound": info["lower_bound"],
                "Upper Bound": info["upper_bound"],
            }
            for col, info in outliers_data.items()
        ])
        st.dataframe(out_df, use_container_width=True)
    else:
        st.success("✅ No significant outliers detected.")

    top_corr = profile.get("top_correlations", [])
    strong_corr = [c for c in top_corr if abs(c["r"]) >= 0.7]
    if strong_corr:
        st.markdown('<p class="section-header">Strong Correlations (|r| ≥ 0.7)</p>', unsafe_allow_html=True)
        corr_df = pd.DataFrame([
            {"Column A": c["col_a"], "Column B": c["col_b"], "r": c["r"], "Direction": c["direction"]}
            for c in strong_corr
        ])
        st.dataframe(corr_df, use_container_width=True)

# ── Tab 3: Insights ──────────────────────────────────────────────
with tab3:
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(f"### 💡 {len(ctx.insights)} AI-Generated Insights")
        st.caption("Powered by Groq · llama-3.1-8b-instant")

    st.markdown("<hr>", unsafe_allow_html=True)

    for i, insight in enumerate(ctx.insights, 1):
        st.markdown(
            f'<div class="insight-card"><strong>{i}.</strong> {insight}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown(f"### 🎯 {len(ctx.recommendations)} Recommendations")
    st.caption("Prioritized actions based on analysis findings.")
    st.markdown("<hr>", unsafe_allow_html=True)

    for i, rec in enumerate(ctx.recommendations, 1):
        severity = _rec_severity(rec)
        css_class = f"rec-card-{severity}"
        icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "🔵"
        st.markdown(
            f'<div class="{css_class}">{icon} <strong>{i}.</strong> {rec}</div>',
            unsafe_allow_html=True,
        )

# ── Tab 4: Charts ────────────────────────────────────────────────
with tab4:
    st.markdown("### 📈 Interactive Charts")
    st.caption("Auto-generated based on your dataset's most interesting patterns.")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Histograms
    if numeric_cols:
        st.markdown('<p class="section-header">Distributions</p>', unsafe_allow_html=True)
        cols_to_show = numeric_cols[:6]
        grid = st.columns(2)
        for i, col in enumerate(cols_to_show):
            grid[i % 2].plotly_chart(
                _make_plotly_histogram(df, col),
                use_container_width=True,
                key=f"hist_{col}",
            )

    # Outlier box plots
    outlier_cols = list(profile.get("outliers", {}).keys())[:4]
    if outlier_cols:
        st.markdown('<p class="section-header">Outlier Columns</p>', unsafe_allow_html=True)
        grid = st.columns(2)
        for i, col in enumerate(outlier_cols):
            grid[i % 2].plotly_chart(
                _make_plotly_box(df, col),
                use_container_width=True,
                key=f"box_{col}",
            )

    # Scatter plots for strong correlations
    strong_pairs = [c for c in profile.get("top_correlations", []) if abs(c["r"]) >= 0.5][:3]
    if strong_pairs:
        st.markdown('<p class="section-header">Correlations</p>', unsafe_allow_html=True)
        grid = st.columns(2)
        for i, pair in enumerate(strong_pairs):
            col_a, col_b = pair["col_a"], pair["col_b"]
            if col_a in df.columns and col_b in df.columns:
                grid[i % 2].plotly_chart(
                    _make_plotly_scatter(df, col_a, col_b, pair["r"]),
                    use_container_width=True,
                    key=f"scatter_{col_a}_{col_b}",
                )

    # Correlation heatmap
    if len(numeric_cols) >= 2:
        st.markdown('<p class="section-header">Correlation Heatmap</p>', unsafe_allow_html=True)
        st.plotly_chart(
            _make_plotly_heatmap(df, numeric_cols),
            use_container_width=True,
            key="heatmap",
        )

    # Bar charts for categoricals
    useful_cat = [c for c in cat_cols if 2 <= profile["categorical_stats"][c]["unique_count"] <= 20][:4]
    if useful_cat:
        st.markdown('<p class="section-header">Categorical Distributions</p>', unsafe_allow_html=True)
        grid = st.columns(2)
        for i, col in enumerate(useful_cat):
            grid[i % 2].plotly_chart(
                _make_plotly_bar(df, col),
                use_container_width=True,
                key=f"bar_{col}",
            )

# ── Tab 5: Report ────────────────────────────────────────────────
with tab5:
    st.markdown("### 📄 Full Analysis Report")
    st.markdown("<hr>", unsafe_allow_html=True)

    if ctx.report_path and os.path.exists(ctx.report_path):
        with open(ctx.report_path, "r", encoding="utf-8") as f:
            content = f.read()

        st.download_button(
            label="📥 Download Report (.md)",
            data=content,
            file_name=f"{ctx.file_name}_analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
            type="primary",
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(content)
    else:
        st.info("Report not available.")
