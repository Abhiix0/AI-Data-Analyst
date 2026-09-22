"""Automated Dataset Briefing and Proactive Discovery Engine."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
import polars as pl
from pydantic import BaseModel, Field

from packages.analytics.tools.schema import inspect_schema
from packages.analytics.tools.distribution import describe_column
from packages.analytics.tools.missingness import calculate_missingness
from packages.analytics.tools.correlation import calculate_correlation
from packages.analytics.tools.outliers import detect_outliers
from packages.analytics.tools.duplicates import count_duplicate_rows
from packages.evidence.models import Finding
from packages.evidence.builders import (
    build_correlation_finding,
    build_outlier_finding,
    build_missingness_finding,
    build_distribution_finding,
)
from packages.visualization.models import ChartSpec
from packages.visualization.selector import generate_chart_specs_from_df
from packages.shared.llm_provider import BaseLLMProvider, LLMMessage


class DatasetBriefing(BaseModel):
    """Complete proactive briefing package generated automatically for a dataset."""
    title: str = "Dataset Executive Briefing"
    summary: str
    row_count: int
    column_count: int
    findings: List[Finding] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommended_charts: List[ChartSpec] = Field(default_factory=list)


def generate_briefing(
    df: pl.DataFrame,
    dataset_version_id: Optional[uuid.UUID] = None,
    analysis_run_id: Optional[uuid.UUID] = None,
    llm: Optional[BaseLLMProvider] = None,
) -> DatasetBriefing:
    """Run full proactive discovery over a Polars DataFrame."""
    version_id = dataset_version_id or uuid.uuid4()
    row_count = len(df)
    col_count = len(df.columns)

    if row_count == 0 or col_count == 0:
        return DatasetBriefing(
            summary="Empty dataset.",
            row_count=0,
            column_count=0,
            findings=[],
            recommendations=["Upload a non-empty dataset."],
            recommended_charts=[],
        )

    findings: List[Finding] = []

    # 1. Missingness Findings
    missing_dict = calculate_missingness(df)
    for col_name, miss in missing_dict.items():
        if miss.pct >= 5.0:
            findings.append(
                build_missingness_finding(
                    missing=miss,
                    dataset_version_id=version_id,
                    analysis_run_id=analysis_run_id,
                )
            )

    # 2. Outliers & Distribution Findings
    for col in df.columns:
        if df[col].dtype.is_numeric():
            outl = detect_outliers(df, col)
            if outl and outl.pct >= 2.0:
                findings.append(
                    build_outlier_finding(
                        outlier=outl,
                        dataset_version_id=version_id,
                        analysis_run_id=analysis_run_id,
                    )
                )

            stat = describe_column(df, col)
            if stat and abs(stat.skew) > 1.5:
                findings.append(
                    build_distribution_finding(
                        stat=stat,
                        dataset_version_id=version_id,
                        analysis_run_id=analysis_run_id,
                    )
                )

    # 3. Correlation Findings
    corr_pairs = calculate_correlation(df, limit=3)
    for corr in corr_pairs:
        findings.append(
            build_correlation_finding(
                pair=corr,
                n=row_count,
                dataset_version_id=version_id,
                analysis_run_id=analysis_run_id,
            )
        )

    # 4. Duplicates
    dup_stats = count_duplicate_rows(df)
    dup_count = dup_stats.duplicate_rows

    # 5. Visualizations
    charts = generate_chart_specs_from_df(df, max_charts=6)

    # 6. Recommendations & Summary
    recommendations: List[str] = []
    if dup_count > 0:
        recommendations.append(f"De-duplicate dataset: {dup_count} exact duplicate rows identified.")
    if any(m.pct > 20.0 for m in missing_dict.values()):
        recommendations.append("Address high missingness columns via imputation or deletion before modeling.")
    if any(f.category == "outlier" for f in findings):
        recommendations.append("Apply robust scaling or capping to outlier-prone numeric columns.")
    if not recommendations:
        recommendations.append("Dataset is clean with zero duplicate rows and low missingness.")

    summary = (
        f"Dataset contains {row_count:,} records across {col_count} columns. "
        f"Identified {len(findings)} key statistical findings and {dup_count} duplicate rows."
    )

    # Optional LLM Enhancement for recommendations
    if llm and not hasattr(llm, "canned_responses"):
        try:
            findings_bullets = "\n".join([f"- {f.claim}" for f in findings[:5]])
            prompt = (
                f"You are a Principal Data Analyst.\n"
                f"Dataset Summary: {summary}\n"
                f"Key Findings:\n{findings_bullets}\n\n"
                "Provide 3 concise, actionable strategic business or analytical recommendations."
            )
            resp = llm.generate([LLMMessage(role="user", content=prompt)])
            llm_recs = [line.strip("- *0123456789.") for line in resp.content.split("\n") if line.strip()]
            if llm_recs:
                recommendations = llm_recs[:4]
        except Exception:
            pass

    return DatasetBriefing(
        summary=summary,
        row_count=row_count,
        column_count=col_count,
        findings=findings,
        recommendations=recommendations,
        recommended_charts=charts,
    )
