from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tempfile
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from orchestrator import run_pipeline

st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")

if "result" not in st.session_state:
    st.session_state.result = None
if "df" not in st.session_state:
    st.session_state.df = None


def save_upload(uploaded_file) -> str:
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 AI Data Analyst")
    st.markdown("---")
    st.markdown("Upload any CSV or Excel dataset and get AI-powered insights, charts, and a full report.")
    st.markdown("---")
    uploaded = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])
    if uploaded:
        st.success(f"✅ {uploaded.name}")
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            path = save_upload(uploaded)
            try:
                with st.spinner("Analysing your data..."):
                    result = run_pipeline(path)
                    df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
                    st.session_state.result = result
                    st.session_state.df = df
                st.success(f"✅ {len(result['insights'])} insights generated!")
            except Exception as e:
                st.error(f"❌ {e}")
    else:
        st.info("👆 Upload a file to get started.")

# ── Empty state ───────────────────────────────────────────────────
if st.session_state.result is None:
    st.title("AI Data Analyst")
    st.markdown("""
Drop any dataset and get a complete analysis:
- **Overview** — what is this data, how big is it
- **Data Quality** — missing values, duplicates, outliers
- **Insights** — AI-written findings grounded in the numbers
- **Charts** — smart visualizations based on what's interesting
- **Report** — full markdown report you can download
""")
    st.stop()

result = st.session_state.result
df = st.session_state.df
profile_metrics = result["profile"]["metrics"]

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Overview", "🔍 Data Quality", "💡 Insights", "📈 Charts", "📄 Report"])

# ── Tab 1: Overview ───────────────────────────────────────────────
with tab1:
    st.header("Dataset Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Insights", len(result["insights"]))
    c4.metric("Recommendations", len(result["recommendations"]))
    st.markdown("---")
    st.markdown(f"**What is this dataset?**\n\n{result['dataset_context']['summary']}")
    for detail in result["dataset_context"].get("insights", []):
        st.markdown(f"- {detail}")
    st.markdown("---")
    st.subheader("Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

# ── Tab 2: Data Quality ───────────────────────────────────────────
with tab2:
    st.header("Data Quality")
    col1, col2, col3 = st.columns(3)
    col1.metric("Missing Columns", len(profile_metrics["missing"]))
    col2.metric("Duplicate Rows", profile_metrics["duplicate_rows"])
    col3.metric("Outlier Columns", len(profile_metrics["outliers"]))
    st.markdown("---")

    missing = profile_metrics["missing"]
    if missing:
        st.subheader("Missing Values")
        rows_data = [[col, info["count"], f"{info['pct']}%"] for col, info in missing.items()]
        st.dataframe(
            pd.DataFrame(rows_data, columns=["Column", "Missing Count", "Missing %"]),
            use_container_width=True,
        )
    else:
        st.success("✅ No missing values!")

    if profile_metrics["duplicate_rows"] > 0:
        st.warning(f"⚠️ {profile_metrics['duplicate_rows']:,} duplicate rows detected.")
    else:
        st.success("✅ No duplicate rows!")

    outliers = profile_metrics["outliers"]
    if outliers:
        st.subheader("Outliers (IQR Method)")
        rows_data = [
            [col, info["count"], f"{info['pct']}%", info["lower_bound"], info["upper_bound"]]
            for col, info in outliers.items()
        ]
        st.dataframe(
            pd.DataFrame(rows_data, columns=["Column", "Count", "%", "Lower Bound", "Upper Bound"]),
            use_container_width=True,
        )
    else:
        st.success("✅ No significant outliers!")

    top_corr = profile_metrics["top_correlations"]
    strong_corr = [c for c in top_corr if abs(c["r"]) >= 0.7]
    if strong_corr:
        st.subheader("Strong Correlations (|r| ≥ 0.7)")
        rows_data = [[c["col_a"], c["col_b"], c["r"], c["direction"]] for c in strong_corr]
        st.dataframe(
            pd.DataFrame(rows_data, columns=["Column A", "Column B", "r", "Direction"]),
            use_container_width=True,
        )

# ── Tab 3: Insights ───────────────────────────────────────────────
with tab3:
    st.header(f"Insights ({len(result['insights'])})")
    st.markdown("*AI-generated insights grounded in your data's statistics.*")
    st.markdown("---")
    for i, insight in enumerate(result["insights"], 1):
        st.markdown(f"**{i}.** {insight}")
        st.markdown("")
    st.markdown("---")
    st.header(f"Recommendations ({len(result['recommendations'])})")
    st.markdown("*Prioritized actions based on the analysis.*")
    st.markdown("---")
    for i, rec in enumerate(result["recommendations"], 1):
        st.markdown(f"**{i}.** {rec}")
        st.markdown("")

# ── Tab 4: Charts ─────────────────────────────────────────────────
with tab4:
    st.header("Visualizations")
    charts = result.get("chart_paths", [])
    if not charts:
        st.info("No charts were generated.")
    else:
        st.markdown(f"*{len(charts)} charts generated based on the most interesting findings.*")
        cols = st.columns(2)
        for i, path in enumerate(charts):
            if os.path.exists(path):
                cols[i % 2].image(path, caption=os.path.basename(path), use_container_width=True)

# ── Tab 5: Report ─────────────────────────────────────────────────
with tab5:
    st.header("Full Report")
    report_path = result.get("report_path")
    if report_path and os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.download_button(
            "📥 Download Report (.md)",
            data=content,
            file_name="analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.markdown("---")
        st.markdown(content)
    else:
        st.info("No report available.")
