import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""AI Data Analyst Streamlit Dashboard."""

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from orchestrator import run_pipeline

# Page configuration
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
)

# Initialize session state
if "pipeline_result" not in st.session_state:
    st.session_state["pipeline_result"] = None
if "df" not in st.session_state:
    st.session_state["df"] = None


def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temporary directory and return path."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return temp_path


def run_analysis_pipeline(file_path: str) -> bool:
    """Run the analysis pipeline and store results in session state."""
    try:
        with st.spinner("Running full analysis pipeline..."):
            result = run_pipeline(file_path)
            
            # Load the dataframe for preview
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:  # Excel files
                df = pd.read_excel(file_path)
            
            # Store in session state
            st.session_state["pipeline_result"] = result
            st.session_state["df"] = df
            
            return True
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return False


def render_overview_tab():
    """Render the Overview tab."""
    if not st.session_state["pipeline_result"]:
        st.info("👈 Upload a file and run analysis to see the overview.")
        return
    
    result = st.session_state["pipeline_result"]
    df = st.session_state["df"]
    
    st.header("📋 Dataset Overview")
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", f"{df.shape[0]:,}")
    with col2:
        st.metric("Columns", df.shape[1])
    with col3:
        dup_rows = result["metrics"]["data_cleaning"].get("duplicate_rows", 0)
        st.metric("Duplicate Rows", f"{dup_rows:,}")
    with col4:
        st.metric("Insights Generated", len(result["insights"]))
    
    # Dataset context summary
    st.subheader("📝 Dataset Summary")
    dataset_summary = result["dataset_context"]["summary"]
    st.info(dataset_summary)
    
    # Data preview
    st.subheader("👁️ Data Preview")
    st.dataframe(df.head(20), use_container_width=True)


def render_data_quality_tab():
    """Render the Data Quality tab."""
    if not st.session_state["pipeline_result"]:
        st.info("👈 Upload a file and run analysis to see data quality information.")
        return
    
    result = st.session_state["pipeline_result"]
    df = st.session_state["df"]
    
    st.header("🔍 Data Quality Analysis")
    
    # Missing values
    st.subheader("📉 Missing Values")
    missing_data = []
    
    # Get missing values from the dataframe
    missing_counts = df.isnull().sum()
    missing_percentages = (df.isnull().sum() / len(df) * 100).round(2)
    
    for col in df.columns:
        if missing_counts[col] > 0:
            missing_data.append({
                "Column": col,
                "Missing Count": missing_counts[col],
                "Missing %": f"{missing_percentages[col]}%"
            })
    
    if missing_data:
        missing_df = pd.DataFrame(missing_data)
        st.dataframe(missing_df, use_container_width=True)
    else:
        st.success("✅ No missing values detected in the dataset!")
    
    # Duplicate rows
    st.subheader("🔄 Duplicate Rows")
    dup_rows = result["metrics"]["data_cleaning"].get("duplicate_rows", 0)
    if dup_rows > 0:
        st.warning(f"⚠️ Found {dup_rows:,} duplicate rows in the dataset.")
    else:
        st.success("✅ No duplicate rows found!")
    
    # Outlier analysis
    st.subheader("🎯 Outlier Analysis")
    outlier_report = result["metrics"]["outliers"].get("outlier_report", {})
    
    if outlier_report:
        outlier_data = []
        for col, info in outlier_report.items():
            outlier_data.append({
                "Column": col,
                "Outlier Count": info["count"],
                "Outlier %": f"{info['percentage']}%",
                "Lower Bound": info["lower_bound"],
                "Upper Bound": info["upper_bound"]
            })
        
        outlier_df = pd.DataFrame(outlier_data)
        st.dataframe(outlier_df, use_container_width=True)
        
        total_outliers = sum(info["count"] for info in outlier_report.values())
        st.info(f"📊 Total outliers detected: {total_outliers:,} across {len(outlier_report)} columns")
    else:
        st.success("✅ No significant outliers detected!")


def render_insights_tab():
    """Render the Insights tab."""
    if not st.session_state["pipeline_result"]:
        st.info("👈 Upload a file and run analysis to see insights.")
        return
    
    result = st.session_state["pipeline_result"]
    
    st.header("💡 Insights & Recommendations")
    
    insights = result["insights"]
    
    if not insights:
        st.info("No insights generated.")
        return
    
    st.subheader(f"📝 {len(insights)} Insights Found")
    
    for i, insight in enumerate(insights, 1):
        with st.container():
            st.info(f"**{i}.** {insight}")
            st.divider()


def render_charts_tab():
    """Render the Charts tab."""
    if not st.session_state["pipeline_result"]:
        st.info("👈 Upload a file and run analysis to see charts.")
        return
    
    result = st.session_state["pipeline_result"]
    chart_paths = result.get("chart_paths", [])
    
    st.header("📈 Data Visualizations")
    
    if not chart_paths:
        st.info("No charts were generated.")
        return
    
    st.subheader(f"📊 {len(chart_paths)} Charts Generated")
    
    # Display charts in 2-column grid
    cols = st.columns(2)
    for i, chart_path in enumerate(chart_paths):
        if os.path.exists(chart_path):
            with cols[i % 2]:
                chart_name = os.path.basename(chart_path)
                st.image(chart_path, caption=chart_name, use_container_width=True)
        else:
            with cols[i % 2]:
                st.error(f"Chart not found: {chart_path}")


def render_report_tab():
    """Render the Report tab."""
    if not st.session_state["pipeline_result"]:
        st.info("👈 Upload a file and run analysis to see the report.")
        return
    
    result = st.session_state["pipeline_result"]
    report_path = result.get("report_path")
    
    st.header("📄 Analysis Report")
    
    if not report_path or not os.path.exists(report_path):
        st.info("No report generated.")
        return
    
    # Read and display the report
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_content = f.read()
        
        st.subheader("📋 Full Analysis Report")
        st.markdown(report_content)
        
        # Download button
        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download Report (.md)",
                data=f.read(),
                file_name="analysis_report.md",
                mime="text/markdown"
            )
    
    except Exception as e:
        st.error(f"Error reading report: {str(e)}")


def main():
    """Main dashboard application."""
    st.title("🤖 AI Data Analyst")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Data Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a dataset file",
            type=["csv", "xlsx", "xls"],
            help="Upload a CSV or Excel file to analyze"
        )
        
        st.markdown("---")
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            if st.button("🚀 Run Analysis", type="primary"):
                # Save uploaded file
                temp_path = save_uploaded_file(uploaded_file)
                
                # Run analysis
                if run_analysis_pipeline(temp_path):
                    result = st.session_state["pipeline_result"]
                    insights_count = len(result["insights"])
                    st.success(f"🎉 Analysis complete! Generated {insights_count} insights.")
        else:
            st.info("👈 Upload a file to get started")
    
    # Main content area
    if st.session_state["pipeline_result"] is None:
        # Empty state
        st.markdown("""
        ## 🎯 Welcome to AI Data Analyst
        
        Upload your dataset and run a comprehensive analysis to get:
        - 📊 Data quality assessment
        - 💡 AI-powered insights
        - 📈 Interactive visualizations  
        - 📄 Detailed reports
        
        **Get started by uploading a file in the sidebar →**
        """)
    else:
        # Tabbed interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Overview", "🔍 Data Quality", "💡 Insights", "📈 Charts", "📄 Report"
        ])
        
        with tab1:
            render_overview_tab()
        
        with tab2:
            render_data_quality_tab()
        
        with tab3:
            render_insights_tab()
        
        with tab4:
            render_charts_tab()
        
        with tab5:
            render_report_tab()


if __name__ == "__main__":
    main()
