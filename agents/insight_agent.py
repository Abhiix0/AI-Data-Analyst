"""Insight Agent — converts statistical findings into human-readable insights."""

import pandas as pd


class InsightAgent:
    """Produces readable insight strings from profiling, pattern, and outlier data."""

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
        print("[Insight Agent] Generating insights...")
        insights = []

        # ── Dataset overview insights ───────────────────────────
        rows = profile["shape"]["rows"]
        cols = profile["shape"]["columns"]
        insights.append(f"The dataset contains {rows:,} rows and {cols} columns.")

        # ── Missing values ──────────────────────────────────────
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

        # ── Duplicates ──────────────────────────────────────────
        dups = profile["duplicate_rows"]
        if dups > 0:
            insights.append(f"There are {dups:,} duplicate rows that may need attention.")

        # ── Correlation insights ────────────────────────────────
        for corr in patterns.get("strong_correlations", []):
            insights.append(
                f"Strong {corr['direction']} correlation ({corr['correlation']}) "
                f"detected between '{corr['column_a']}' and '{corr['column_b']}'."
            )

        # ── Trend insights ──────────────────────────────────────
        for trend in patterns.get("column_trends", []):
            insights.append(
                f"Column '{trend['column']}' shows an {trend['trend']} trend "
                f"({trend['change_percent']:+.1f}% change between first and second half of data)."
            )

        # ── Outlier insights ────────────────────────────────────
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

        # ── Categorical insights ────────────────────────────────
        for col, summary in profile.get("categorical_summary", {}).items():
            if summary["unique_values"] <= 2:
                insights.append(f"Column '{col}' is nearly binary with only {summary['unique_values']} unique value(s).")

        print(f"[Insight Agent] Generated {len(insights)} insights")
        return insights
