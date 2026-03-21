"""Report Agent — assembles everything into a structured markdown report."""
from __future__ import annotations
from typing import Dict, Any, List
import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "reports")


def run(
    source: str,
    context: Dict[str, Any],
    profile: Dict[str, Any],
    insights: List[str],
    recommendations: List[str],
    charts: List[str],
) -> Dict[str, Any]:
    """Assemble the full markdown report from all agent outputs."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    m = profile["metrics"]
    shape = m["shape"]
    missing = m["missing"]
    outliers = m["outliers"]
    top_corr = m["top_correlations"]

    lines = []
    lines += [
        "# AI Data Analyst — Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Dataset:** `{source}`",
        "",
        "---",
        "## 1. Dataset Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Rows | {shape['rows']:,} |",
        f"| Columns | {shape['columns']} |",
        f"| Duplicate Rows | {m['duplicate_rows']:,} |",
        f"| Missing Columns | {len(missing)} |",
        f"| Outlier Columns | {len(outliers)} |",
        "",
        f"**Dataset Summary:** {context.get('summary', 'N/A')}",
        "",
    ]

    # Column types
    lines += ["### Column Types", "", "| Column | Type |", "|--------|------|"]
    for col, dtype in m["dtypes"].items():
        lines.append(f"| {col} | {dtype} |")
    lines.append("")

    # Data quality
    lines += ["---", "## 2. Data Quality", ""]
    if missing:
        lines += ["### Missing Values", "", "| Column | Missing Count | Missing % |", "|--------|--------------|-----------|"]
        for col, info in missing.items():
            lines.append(f"| {col} | {info['count']:,} | {info['pct']}% |")
        lines.append("")
    else:
        lines += ["✅ No missing values.", ""]

    if m["duplicate_rows"] > 0:
        lines += [f"⚠️ **{m['duplicate_rows']:,} duplicate rows** detected.", ""]

    if outliers:
        lines += ["### Outliers", "", "| Column | Count | % | Lower Bound | Upper Bound |", "|--------|-------|---|-------------|-------------|"]
        for col, info in outliers.items():
            lines.append(f"| {col} | {info['count']} | {info['pct']}% | {info['lower_bound']} | {info['upper_bound']} |")
        lines.append("")
    else:
        lines += ["✅ No significant outliers.", ""]

    # Correlations
    if top_corr:
        strong = [c for c in top_corr if abs(c["r"]) >= 0.7]
        if strong:
            lines += ["### Strong Correlations (|r| >= 0.7)", "", "| Column A | Column B | r | Direction |", "|----------|----------|---|-----------|"]
            for c in strong:
                lines.append(f"| {c['col_a']} | {c['col_b']} | {c['r']} | {c['direction']} |")
            lines.append("")

    # Insights
    lines += ["---", "## 3. Key Insights", ""]
    for i, insight in enumerate(insights, 1):
        lines.append(f"{i}. {insight}")
    lines.append("")

    # Recommendations
    lines += ["---", "## 4. Recommendations", ""]
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    # Charts
    lines += ["---", "## 5. Visualizations", ""]
    if charts:
        for path in charts:
            name = os.path.basename(path)
            rel = os.path.relpath(path, REPORTS_DIR).replace("\\", "/")
            lines += [f"### {name}", f"![{name}]({rel})", ""]
    else:
        lines += ["No charts generated.", ""]

    report_path = os.path.join(REPORTS_DIR, "analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "summary": f"Report saved to {report_path}.",
        "metrics": {"report_path": report_path},
        "insights": [f"Report written to {report_path}."],
        "report_path": report_path,
    }
