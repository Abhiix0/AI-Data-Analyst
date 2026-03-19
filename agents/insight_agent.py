"""Insight Agent — generates intelligent insights using LLM when available, with rule-based fallback."""

from __future__ import annotations

from typing import Dict, Any, List

import json
import pandas as pd

from llm.claude_client import generate, is_available, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import (
    INSIGHT_SYSTEM_PROMPT,
    insight_prompt,
    structured_summary_from_metrics,
)


class InsightAgent:
    """Generates professional data analysis insights using LLM reasoning with rule-based fallback."""

    def __init__(self, model: str = DEFAULT_MODEL, use_llm: bool = True):
        """Initialize the Insight Agent.
        
        Args:
            model: Name of the Ollama model to use (default: llama3)
            use_llm: Whether to use LLM or fall back to rule-based (default: True)
        """
        self.model = model
        self.use_llm = use_llm and is_available()
        if self.use_llm:
            print(f"[Insight Agent] Using LLM model via centralized client: {self.model}")
        else:
            print("[Insight Agent] LLM unavailable — using rule-based insights.")

    def run(self, df: pd.DataFrame, profile: dict, patterns: dict, outliers: dict) -> list[str]:
        """Generate insights from analysis results.

        Args:
            df: Input DataFrame.
            profile: Output from ProfilingAgent.
            patterns: Output from PatternDetectionAgent.
            outliers: Output from OutlierDetectionAgent.

        Returns:
            List of human-readable insight strings.
        """
        if self.use_llm:
            return self._generate_llm_insights(df, profile, patterns, outliers)
        return self._generate_rule_based_insights(profile, patterns, outliers)

    def _generate_llm_insights(self, df: pd.DataFrame, profile: dict, patterns: dict, outliers: dict) -> list[str]:
        """Generate insights using LLM reasoning.
        
        Args:
            df: Input DataFrame (used for sample data only)
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            
        Returns:
            List of insight strings
        """
        print("[Insight Agent - LLM] Generating AI-powered insights via centralized client...")

        # Build structured summary for LLM
        summary = self._build_dataset_summary(df, profile, patterns, outliers)
        summary_text = json.dumps(summary, indent=2, default=str)

        # Create prompt for LLM using the shared prompt template
        prompt = insight_prompt(summary_text)

        try:
            insights_text = generate(
                prompt=prompt,
                model=self.model,
                system_prompt=INSIGHT_SYSTEM_PROMPT,
            )
            insights = self._parse_llm_response(insights_text)

            print(f"[Insight Agent - LLM] Generated {len(insights)} AI-powered insights")
            return insights

        except (LLMUnavailableError, RuntimeError) as e:
            print(f"⚠️ LLM generation failed via centralized client: {e}")
            print("[Insight Agent] Falling back to rule-based insights...")
            return self._generate_rule_based_insights(profile, patterns, outliers)

    def _build_dataset_summary(self, df: pd.DataFrame, profile: dict, patterns: dict, outliers: dict) -> dict:
        """Build a structured summary of the dataset for LLM analysis.
        
        Args:
            df: Input DataFrame
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            
        Returns:
            Dictionary with dataset summary
        """
        # Get sample rows (first 3 rows, excluding large text columns)
        sample_data = {}
        for col in df.columns[:10]:  # Limit to first 10 columns
            if df[col].dtype in ['object', 'string']:
                # For text columns, show only first 50 chars
                sample_data[col] = [str(val)[:50] for val in df[col].head(3).tolist()]
            else:
                sample_data[col] = df[col].head(3).tolist()
        
        summary = {
            "dataset_size": {
                "rows": profile["shape"]["rows"],
                "columns": profile["shape"]["columns"]
            },
            "column_types": profile["dtypes"],
            "missing_values": {
                col: {
                    "count": profile["missing_values"][col],
                    "percentage": profile["missing_percentage"][col]
                }
                for col in profile["missing_values"]
                if profile["missing_values"][col] > 0
            },
            "duplicate_rows": profile["duplicate_rows"],
            "numeric_columns": list(profile.get("numeric_stats", {}).keys()),
            "categorical_columns": list(profile.get("categorical_summary", {}).keys()),
            "numeric_statistics": profile.get("numeric_stats", {}),
            "categorical_summary": profile.get("categorical_summary", {}),
            "strong_correlations": patterns.get("strong_correlations", []),
            "trends": patterns.get("column_trends", []),
            "outliers": outliers,
            "sample_data": sample_data
        }
        
        return summary

    def _create_analysis_prompt(self, summary: dict) -> str:
        """Create a detailed prompt for the LLM.
        
        Args:
            summary: Dataset summary dictionary
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following dataset and provide professional data analysis insights.

DATASET OVERVIEW:
- Total Rows: {summary['dataset_size']['rows']:,}
- Total Columns: {summary['dataset_size']['columns']}
- Duplicate Rows: {summary['duplicate_rows']}

COLUMN INFORMATION:
- Numeric Columns ({len(summary['numeric_columns'])}): {', '.join(summary['numeric_columns'][:10])}
- Categorical Columns ({len(summary['categorical_columns'])}): {', '.join(summary['categorical_columns'][:10])}

DATA QUALITY:
"""
        
        if summary['missing_values']:
            prompt += "Missing Values:\n"
            for col, info in list(summary['missing_values'].items())[:5]:
                prompt += f"  - {col}: {info['count']} missing ({info['percentage']}%)\n"
        else:
            prompt += "- No missing values detected\n"
        
        if summary['strong_correlations']:
            prompt += "\nSTRONG CORRELATIONS:\n"
            for corr in summary['strong_correlations'][:5]:
                prompt += f"  - {corr['column_a']} ↔ {corr['column_b']}: {corr['correlation']} ({corr['direction']})\n"
        
        if summary['trends']:
            prompt += "\nTRENDS DETECTED:\n"
            for trend in summary['trends'][:5]:
                prompt += f"  - {trend['column']}: {trend['trend']} ({trend['change_percent']:+.1f}%)\n"
        
        if summary['outliers']:
            prompt += "\nOUTLIERS DETECTED:\n"
            for col, info in list(summary['outliers'].items())[:5]:
                prompt += f"  - {col}: {info['count']} outliers ({info['percentage']}%)\n"
        
        # Add sample data
        if summary['sample_data']:
            prompt += "\nSAMPLE DATA (first 3 rows):\n"
            prompt += json.dumps(summary['sample_data'], indent=2)[:500]  # Limit size
        
        prompt += """

TASK:
As a professional data analyst, provide 5-8 key insights about this dataset. Focus on:
1. Data quality issues and their implications
2. Interesting patterns and correlations
3. Potential anomalies or outliers
4. Business or analytical implications
5. Relationships between variables
6. Data distribution characteristics

Format your response as a numbered list of clear, concise insights. Each insight should be one sentence.
Do not include explanations or recommendations - only factual insights about what the data shows.

INSIGHTS:"""
        
        return prompt

    def _parse_llm_response(self, response_text: str) -> list[str]:
        """Backward-compatible instance wrapper around the shared parser helper."""
        return _parse_bullet_list_response(response_text)

    def _generate_rule_based_insights(self, profile: dict, patterns: dict, outliers: dict) -> list[str]:
        """Fallback to rule-based insights if LLM is unavailable.
        
        Args:
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            
        Returns:
            List of insight strings
        """
        print("[Insight Agent - Rule Based] Generating rule-based insights...")
        insights = []

        # Dataset overview
        rows = profile["shape"]["rows"]
        cols = profile["shape"]["columns"]
        insights.append(f"The dataset contains {rows:,} rows and {cols} columns.")

        # Missing values
        missing = {k: v for k, v in profile["missing_values"].items() if v > 0}
        if missing:
            worst_col = max(missing, key=missing.get)
            pct = profile["missing_percentage"][worst_col]
            insights.append(
                f"{len(missing)} column(s) have missing values. "
                f"'{worst_col}' has the most with {missing[worst_col]:,} missing ({pct}%)."
            )
        else:
            insights.append("The dataset has no missing values — data quality is excellent.")

        # Duplicates
        dups = profile["duplicate_rows"]
        if dups > 0:
            insights.append(f"There are {dups:,} duplicate rows that may need attention.")

        # Correlations
        for corr in patterns.get("strong_correlations", []):
            insights.append(
                f"Strong {corr['direction']} correlation ({corr['correlation']}) "
                f"detected between '{corr['column_a']}' and '{corr['column_b']}'."
            )

        # Trends
        for trend in patterns.get("column_trends", []):
            insights.append(
                f"Column '{trend['column']}' shows an {trend['trend']} trend "
                f"({trend['change_percent']:+.1f}% change between first and second half of data)."
            )

        # Outliers
        if outliers:
            total_outliers = sum(info["count"] for info in outliers.values())
            insights.append(
                f"A total of {total_outliers:,} outliers were detected across "
                f"{len(outliers)} column(s)."
            )
            for col, info in outliers.items():
                if info["percentage"] > 5:
                    insights.append(
                        f"Column '{col}' has a high outlier percentage ({info['percentage']}%) "
                        f"— values outside [{info['lower_bound']}, {info['upper_bound']}]."
                    )

        # Categorical insights
        for col, summary in profile.get("categorical_summary", {}).items():
            if summary["unique_values"] <= 2:
                insights.append(f"Column '{col}' is nearly binary with only {summary['unique_values']} unique value(s).")

        print(f"[Insight Agent - Rule Based] Generated {len(insights)} insights")
        return insights


def _parse_bullet_list_response(response_text: str) -> List[str]:
    """Parse a numbered/bulleted list from an LLM response into plain strings."""
    insights: List[str] = []
    lines = response_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove numbering or bullet markers (1., 2., -, *, •, etc.)
        line = line.lstrip("0123456789.-*• ")
        line = line.lstrip(") ")

        if len(line) > 20:  # Filter out very short lines
            insights.append(line)

    return insights


def run(
    df: pd.DataFrame,
    cleaning_result: Dict[str, Any],
    analysis_result: Dict[str, Any],
    dataset_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Phase 1 insight agent entrypoint.

    This function exposes a minimal, function-based interface that fits the
    standardized agent contract used by the new orchestrator:

    {
        "summary": str,
        "metrics": {
            "mean": ...,
            "median": ...,
            "missing_values": ...
        },
        "insights": [str, ...],
    }
    """
    # Build a compact summary string from upstream agent metrics and optional context.
    cleaning_metrics = cleaning_result.get("metrics", {})
    analysis_metrics = analysis_result.get("metrics", {})
    summary_payload = structured_summary_from_metrics(
        cleaning_metrics=cleaning_metrics,
        analysis_metrics=analysis_metrics,
        dataset_context=dataset_context or {},
    )

    insights: List[str]
    try:
        raw_response = generate(
            prompt=insight_prompt(summary_payload),
            model=DEFAULT_MODEL,
            system_prompt=INSIGHT_SYSTEM_PROMPT,
        )
        insights = _parse_bullet_list_response(raw_response)
    except (LLMUnavailableError, RuntimeError):
        # Fall back to echoing upstream agent insights if the LLM is unavailable.
        insights = []
        if dataset_context:
            # Include dataset-level understanding first if available.
            context_summary = dataset_context.get("summary")
            if isinstance(context_summary, str) and context_summary:
                insights.append(context_summary)
            insights.extend(dataset_context.get("insights", []))
        insights.extend(cleaning_result.get("insights", []))
        insights.extend(analysis_result.get("insights", []))
        if not insights:
            insights.append(
                "No additional insights available because the LLM is unavailable and "
                "upstream agents did not provide insights."
            )

    metrics: Dict[str, Any] = {
        # Reuse numeric and missingness metrics from upstream agents so that
        # the orchestrator has a single place to look.
        "mean": analysis_metrics.get("mean"),
        "median": analysis_metrics.get("median"),
        "missing_values": cleaning_metrics.get("missing_values"),
    }

    summary = (
        "Generated high-level narrative insights by combining data cleaning "
        "and basic statistical analysis results."
    )

    return {
        "summary": summary,
        "metrics": metrics,
        "insights": insights,
    }

