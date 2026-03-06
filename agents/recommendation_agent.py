"""Recommendation Agent — generates actionable suggestions based on analysis results."""


class RecommendationAgent:
    """Produces actionable recommendations from insights, patterns, and outliers."""

    def run(self, profile: dict, patterns: dict, outliers: dict, insights: list[str]) -> list[str]:
        """Generate recommendations.

        Args:
            profile: Output from ProfilingAgent.
            patterns: Output from PatternDetectionAgent.
            outliers: Output from OutlierDetectionAgent.
            insights: Output from InsightAgent.

        Returns:
            List of recommendation strings.
        """
        print("[Recommendation Agent] Generating recommendations...")
        recommendations = []

        # ── Missing value recommendations ───────────────────────
        missing = {k: v for k, v in profile["missing_values"].items() if v > 0}
        for col, count in missing.items():
            pct = profile["missing_percentage"][col]
            if pct > 40:
                recommendations.append(
                    f"Consider dropping column '{col}' — {pct}% of values are missing."
                )
            elif pct > 5:
                recommendations.append(
                    f"Impute missing values in '{col}' ({pct}% missing) using mean/median or domain logic."
                )

        # ── Duplicate recommendations ───────────────────────────
        if profile["duplicate_rows"] > 0:
            recommendations.append(
                f"Remove {profile['duplicate_rows']:,} duplicate rows to ensure data integrity."
            )

        # ── Correlation recommendations ─────────────────────────
        for corr in patterns.get("strong_correlations", []):
            recommendations.append(
                f"Investigate the {corr['direction']} relationship between "
                f"'{corr['column_a']}' and '{corr['column_b']}' (r={corr['correlation']}) "
                f"— consider feature engineering or multicollinearity checks."
            )

        # ── Outlier recommendations ─────────────────────────────
        for col, info in outliers.items():
            if info["percentage"] > 5:
                recommendations.append(
                    f"Review outliers in '{col}' ({info['count']} values, {info['percentage']}%) "
                    f"— consider capping, transformation, or removal."
                )

        # ── General recommendations ─────────────────────────────
        numeric_count = len(profile.get("numeric_stats", {}))
        cat_count = len(profile.get("categorical_summary", {}))

        if numeric_count > 0 and cat_count > 0:
            recommendations.append(
                "The dataset has both numeric and categorical features — "
                "consider encoding categorical variables for modeling."
            )

        if not recommendations:
            recommendations.append("The dataset looks clean and ready for further analysis or modeling.")

        print(f"[Recommendation Agent] Generated {len(recommendations)} recommendations")
        return recommendations
