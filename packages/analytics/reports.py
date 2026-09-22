"""Modular report generation engine for structured markdown and standalone HTML reports."""
from __future__ import annotations
import html
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from packages.analytics.briefing import DatasetBriefing
from packages.evidence.models import Evidence, Finding
from packages.visualization.models import ChartSpec
from packages.shared.storage import StorageClient, get_storage_client


class ReportConfig(BaseModel):
    title: str = "AI Data Analyst — Analytical Report"
    include_briefing: bool = True
    include_findings: bool = True
    include_pinned_only: bool = False
    include_investigations: bool = True
    include_evidence_ledger: bool = True
    include_visualizations: bool = True


class ReportGenerator:
    """Compiles findings, briefings, visualizations, and evidence into publication-ready reports."""

    def __init__(
        self,
        dataset_name: str,
        briefing: Optional[DatasetBriefing] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        investigations: Optional[List[Dict[str, Any]]] = None,
        charts: Optional[List[Dict[str, Any]]] = None,
        evidence_ledger: Optional[List[Dict[str, Any]]] = None,
        config: Optional[ReportConfig] = None,
    ):
        self.dataset_name = dataset_name
        self.briefing = briefing
        self.findings = findings or []
        self.investigations = investigations or []
        self.charts = charts or []
        self.evidence_ledger = evidence_ledger or []
        self.config = config or ReportConfig()
        self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def generate_markdown(self) -> str:
        """Generate structured markdown report."""
        lines: List[str] = [
            f"# {self.config.title}",
            "",
            f"**Dataset:** `{self.dataset_name}`  ",
            f"**Generated:** {self.generated_at}  ",
            "",
            "---",
            "",
        ]

        # 1. Executive Summary & Briefing
        if self.config.include_briefing and self.briefing:
            lines += [
                "## 1. Executive Summary & Dataset Health",
                "",
                f"> {self.briefing.summary}",
                "",
                "### Dataset Metrics",
                "",
                "| Metric | Value |",
                "|---|---|",
                f"| **Total Rows** | {self.briefing.row_count:,} |",
                f"| **Total Columns** | {self.briefing.column_count:,} |",
                f"| **Proactive Findings** | {len(self.briefing.findings)} |",
                f"| **Recommended Charts** | {len(self.briefing.recommended_charts)} |",
                "",
            ]

            if self.briefing.recommendations:
                lines += ["### Recommended Actions", ""]
                for i, rec in enumerate(self.briefing.recommendations, 1):
                    lines.append(f"{i}. {rec}")
                lines.append("")

            lines += ["---", ""]

        # 2. Key Analytical Findings
        if self.config.include_findings and self.findings:
            lines += ["## 2. Key Analytical Findings", ""]
            filtered_findings = self.findings
            if self.config.include_pinned_only:
                filtered_findings = [f for f in self.findings if f.get("is_pinned", False)]

            if not filtered_findings:
                lines += ["*No matching findings to display.*", ""]
            else:
                for idx, f in enumerate(filtered_findings, 1):
                    claim = f.get("claim") or f.get("title") or "Finding"
                    strength = (f.get("evidence_strength") or f.get("strength") or "strong").upper()
                    source_cols = f.get("source_columns") or []
                    user_notes = f.get("user_notes")
                    evidence_list = f.get("evidence_json") or []

                    badge = f"**[{strength}]**"
                    lines += [
                        f"### Finding {idx}: {claim}",
                        f"- **Evidence Strength:** {badge}",
                        f"- **Source Columns:** {', '.join(f'`{c}`' for c in source_cols) if source_cols else 'N/A'}",
                    ]
                    if user_notes:
                        lines.append(f"- **User Note:** *\"{user_notes}\"*")
                    if evidence_list:
                        lines.append("- **Supporting Evidence:**")
                        for ev in evidence_list[:3]:
                            metric = ev.get("metric_name", "metric")
                            val = ev.get("value", "")
                            conf = ev.get("confidence_score", 1.0)
                            lines.append(f"  - `{metric}` = **{val}** (confidence: {conf:.0%})")
                    lines.append("")

            lines += ["---", ""]

        # 3. Drill-Down Investigations
        if self.config.include_investigations and self.investigations:
            lines += ["## 3. Drill-Down Investigations & Deep Dives", ""]
            for idx, inv in enumerate(self.investigations, 1):
                query = inv.get("query", "Investigation")
                summary = inv.get("summary") or "Investigation completed."
                count = inv.get("findings_count", 0)
                status = inv.get("status", "completed").upper()

                lines += [
                    f"### Deep Dive {idx}: {query}",
                    f"- **Status:** `{status}` | **New Findings Uncovered:** `{count}`",
                    "",
                    f"{summary}",
                    "",
                ]
            lines += ["---", ""]

        # 4. Visualizations
        if self.config.include_visualizations and self.charts:
            lines += ["## 4. Visualizations & Distributions", ""]
            for idx, chart in enumerate(self.charts, 1):
                title = chart.get("title", f"Visualization {idx}")
                chart_type = chart.get("chart_type", "chart")
                desc = chart.get("description", "")
                lines += [
                    f"### Chart {idx}: {title} (`{chart_type}`)",
                    f"{desc}" if desc else "",
                    "",
                ]
            lines += ["---", ""]

        # 5. Verified Evidence Ledger
        if self.config.include_evidence_ledger and self.evidence_ledger:
            lines += [
                "## 5. Verified Evidence Ledger (Audit Trail)",
                "",
                "| Evidence ID | Metric | Deterministic Value | Query / Tool | Confidence |",
                "|---|---|---|---|---|",
            ]
            for ev in self.evidence_ledger:
                ev_id = str(ev.get("id", ""))[:8]
                metric = ev.get("metric_name", "metric")
                val = str(ev.get("value", ""))
                q = (ev.get("source_query") or ev.get("source_tool") or "tool").replace("|", "/")
                conf = f"{ev.get('confidence_score', 1.0):.0%}"
                lines.append(f"| `{ev_id}` | `{metric}` | **{val}** | `{q}` | {conf} |")
            lines.append("")

        return "\n".join(lines)

    def generate_html(self) -> str:
        """Generate standalone, beautifully styled HTML report with dark/light aesthetics."""
        md_text = self.generate_markdown()
        escaped_title = html.escape(self.config.title)
        escaped_dataset = html.escape(self.dataset_name)

        # Convert markdown sections to simple clean HTML blocks
        html_content = []
        for line in md_text.split("\n"):
            if line.startswith("# "):
                html_content.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "):
                html_content.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("### "):
                html_content.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("> "):
                html_content.append(f"<div class='callout'>{html.escape(line[2:])}</div>")
            elif line.startswith("- "):
                html_content.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.startswith("---"):
                html_content.append("<hr />")
            elif line.strip():
                html_content.append(f"<p>{html.escape(line)}</p>")

        body_inner = "\n".join(html_content)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --success: #34d399;
            --warning: #fbbf24;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 48px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        h1 {{
            color: var(--text-main);
            font-size: 28px;
            margin-top: 0;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 12px;
        }}
        h2 {{
            color: var(--accent);
            font-size: 20px;
            margin-top: 32px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }}
        h3 {{
            color: #e2e8f0;
            font-size: 16px;
            margin-top: 20px;
        }}
        p, li {{
            color: var(--text-main);
            font-size: 14px;
        }}
        .callout {{
            background: var(--accent-glow);
            border-left: 4px solid var(--accent);
            padding: 16px 20px;
            border-radius: 6px;
            margin: 16px 0;
            color: #e2e8f0;
            font-style: italic;
        }}
        hr {{
            border: 0;
            border-top: 1px solid var(--border);
            margin: 32px 0;
        }}
        code {{
            background: #090d16;
            color: #38bdf8;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }}
        th, td {{
            padding: 10px 12px;
            border: 1px solid var(--border);
            text-align: left;
            font-size: 13px;
        }}
        th {{
            background-color: #090d16;
            color: var(--accent);
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
            border-radius: 9999px;
            background: rgba(52, 211, 153, 0.2);
            color: var(--success);
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        {body_inner}
        <div class="footer">
            Generated autonomously by AI Data Analyst &bull; Verified with Deterministic Polars &amp; DuckDB Evidence Gate
        </div>
    </div>
</body>
</html>
"""

    def generate_and_save(
        self,
        run_id: str,
        storage_client: Optional[StorageClient] = None,
    ) -> Dict[str, str]:
        """Generate both Markdown and HTML reports and persist them in storage."""
        client = storage_client or get_storage_client()
        md_content = self.generate_markdown()
        html_content = self.generate_html()

        md_key = f"reports/{run_id}/analysis_report.md"
        html_key = f"reports/{run_id}/analysis_report.html"

        client.upload_bytes(
            key=md_key,
            data=md_content.encode("utf-8"),
            content_type="text/markdown",
        )
        client.upload_bytes(
            key=html_key,
            data=html_content.encode("utf-8"),
            content_type="text/html",
        )

        return {
            "markdown_path": md_key,
            "html_path": html_key,
            "markdown_content": md_content,
            "html_content": html_content,
        }


def generate_report_from_context(ctx: Any) -> str:
    """Legacy backward compatibility bridge for orchestrator context."""
    from packages.shared.storage import get_storage_client
    import os

    generator = ReportGenerator(
        dataset_name=getattr(ctx, "file_name", "dataset"),
        findings=[{"claim": c, "evidence_strength": "strong"} for c in getattr(ctx, "insights", [])],
        charts=getattr(ctx, "chart_paths", []),
    )
    md = generator.generate_markdown()

    out_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(out_dir, exist_ok=True)
    report_file = os.path.join(out_dir, "analysis_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)

    return report_file
