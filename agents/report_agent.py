"""Report Agent — assembles everything into a structured markdown report."""
from __future__ import annotations
import os
from datetime import datetime

from core.context import AnalysisContext

from core.config import REPORTS_DIR


def run(ctx: AnalysisContext) -> str:
    """Writes markdown report. Returns the report file path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    m = ctx.profile
    shape = m["shape"]
    missing = m.get("missing", {})
    outliers = m.get("outliers", {})
    top_corr = m.get("top_correlations", [])

    lines = []
    lines += [
        "# AI Data Analyst — Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Dataset:** `{ctx.file_name}`",
        "",
        "---",
        "## 1. Dataset Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Rows | {shape['rows']:,} |",
        f"| Columns | {shape['columns']} |",
        f"| Duplicate Rows | {m.get('duplicate_rows', 0):,} |",
        f"| Missing Columns | {len(missing)} |",
        f"| Outlier Columns | {len(outliers)} |",
        "",
        f"**Dataset Summary:** {ctx.shape_summary()}",
        "",
    ]

    # Column types
    lines += ["### Column Types", "", "| Column | Type |", "|--------|------|"]
    for col, dtype in m.get("dtypes", {}).items():
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

    if m.get("duplicate_rows", 0) > 0:
        lines += [f"⚠️ **{m['duplicate_rows']:,} duplicate rows** detected.", ""]

    if outliers:
        lines += ["### Outliers", "", "| Column | Count | % | Lower Bound | Upper Bound |", "|--------|-------|---|-------------|-------------|"]
        for col, info in outliers.items():
            lines.append(f"| {col} | {info['count']} | {info['pct']}% | {info['lower_bound']} | {info['upper_bound']} |")
        lines.append("")
    else:
        lines += ["✅ No significant outliers.", ""]

    if top_corr:
        strong = [c for c in top_corr if abs(c["r"]) >= 0.7]
        if strong:
            lines += ["### Strong Correlations (|r| >= 0.7)", "", "| Column A | Column B | r | Direction |", "|----------|----------|---|-----------|"]
            for c in strong:
                lines.append(f"| {c['col_a']} | {c['col_b']} | {c['r']} | {c['direction']} |")
            lines.append("")

    # Insights
    lines += ["---", "## 3. Key Insights", ""]
    for i, insight in enumerate(ctx.insights, 1):
        lines.append(f"{i}. {insight}")
    lines.append("")

    # Recommendations
    lines += ["---", "## 4. Recommendations", ""]
    for i, rec in enumerate(ctx.recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    # Charts
    lines += ["---", "## 5. Visualizations", ""]
    if ctx.chart_paths:
        lines += [
            "> 📁 **Note:** Chart images are saved in `outputs/charts/`.",
            "> To view them, open this report from the project root directory.",
            "",
        ]
        for path in ctx.chart_paths:
            name = os.path.basename(path)
            # Use path relative to project root for portability
            rel = os.path.join("..", "charts", name).replace("\\", "/")
            lines += [f"### {name}", f"![{name}]({rel})", ""]
    else:
        lines += ["No charts generated.", ""]

    report_path = os.path.join(REPORTS_DIR, "analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_path
