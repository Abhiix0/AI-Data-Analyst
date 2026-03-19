"""Report Agent — compiles all analysis outputs into a structured Markdown report."""

import os
from datetime import datetime


REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "reports")


class ReportAgent:
    """Aggregates all agent outputs into a Markdown analysis report."""

    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def run(
        self,
        source: str,
        profile: dict,
        charts: list[str],
        patterns: dict,
        outliers: dict,
        insights: list[str],
        recommendations: list[str],
    ) -> str:
        """Generate the final analysis report.

        Args:
            source: Original dataset source path or reference.
            profile: Output from ProfilingAgent.
            charts: List of chart file paths from VisualizationAgent.
            patterns: Output from PatternDetectionAgent.
            outliers: Output from OutlierDetectionAgent.
            insights: Output from InsightAgent.
            recommendations: Output from RecommendationAgent.

        Returns:
            Path to the saved Markdown report.
        """
        print("[Report Agent] Compiling report...")

        lines = []
        lines.append("# 📊 AI Data Analyst — Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Dataset:** `{source}`")
        lines.append("")

        # ── 1. Dataset Overview ─────────────────────────────────
        lines.append("---")
        lines.append("## 1. Dataset Overview")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Rows | {profile['shape']['rows']:,} |")
        lines.append(f"| Columns | {profile['shape']['columns']} |")
        lines.append(f"| Duplicate Rows | {profile['duplicate_rows']:,} |")
        lines.append("")

        lines.append("### Column Types")
        lines.append("")
        lines.append("| Column | Type |")
        lines.append("|--------|------|")
        for col, dtype in profile["dtypes"].items():
            lines.append(f"| {col} | {dtype} |")
        lines.append("")

        # ── 2. Data Quality Issues ──────────────────────────────
        lines.append("---")
        lines.append("## 2. Data Quality Issues")
        lines.append("")

        missing = {k: v for k, v in profile["missing_values"].items() if v > 0}
        if missing:
            lines.append("### Missing Values")
            lines.append("")
            lines.append("| Column | Missing Count | Missing % |")
            lines.append("|--------|--------------|-----------|")
            for col, count in missing.items():
                pct = profile["missing_percentage"][col]
                lines.append(f"| {col} | {count:,} | {pct}% |")
            lines.append("")
        else:
            lines.append("✅ No missing values detected.")
            lines.append("")

        if profile["duplicate_rows"] > 0:
            lines.append(f"⚠️ **{profile['duplicate_rows']:,} duplicate row(s)** found in the dataset.")
            lines.append("")

        # ── 3. Key Insights ─────────────────────────────────────
        lines.append("---")
        lines.append("## 3. Key Insights")
        lines.append("")
        for i, insight in enumerate(insights, 1):
            lines.append(f"{i}. {insight}")
        lines.append("")

        # ── 4. Outlier Analysis ─────────────────────────────────
        lines.append("---")
        lines.append("## 4. Outlier Analysis")
        lines.append("")
        if outliers:
            lines.append("| Column | Outlier Count | % of Column | Lower Bound | Upper Bound |")
            lines.append("|--------|--------------|-------------|-------------|-------------|")
            for col, info in outliers.items():
                lines.append(
                    f"| {col} | {info['count']} | {info['percentage']}% "
                    f"| {info['lower_bound']} | {info['upper_bound']} |"
                )
            lines.append("")
        else:
            lines.append("✅ No significant outliers detected.")
            lines.append("")

        # ── 5. Visualizations ───────────────────────────────────
        lines.append("---")
        lines.append("## 5. Visualizations")
        lines.append("")
        if charts:
            for chart_path in charts:
                chart_name = os.path.basename(chart_path)
                # Use relative path from reports dir
                rel_path = os.path.relpath(chart_path, REPORTS_DIR).replace("\\", "/")
                lines.append(f"### {chart_name}")
                lines.append(f"![{chart_name}]({rel_path})")
                lines.append("")
        else:
            lines.append("No charts were generated.")
            lines.append("")

        # ── 6. Recommendations ──────────────────────────────────
        lines.append("---")
        lines.append("## 6. Recommendations")
        lines.append("")
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        # ── Save report ─────────────────────────────────────────
        report_path = os.path.join(REPORTS_DIR, "analysis_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[Report Agent] Report saved to {report_path}")
        return report_path


def run(source: str, profile: dict, charts: list, patterns: dict, outliers: dict, insights: list, recommendations: list) -> dict:
    """Module-level entry point — consistent with other agents."""
    agent = ReportAgent()
    report_path = agent.run(source, profile, charts, patterns, outliers, insights, recommendations)
    return {
        "summary": f"Report saved to {report_path}.",
        "metrics": {"report_path": report_path},
        "insights": [f"Full analysis report written to {report_path}."],
        "report_path": report_path,
    }
