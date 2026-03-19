"""Outlier Detection Agent — detects anomalies using the IQR method."""

import pandas as pd


class OutlierDetectionAgent:
    """Detects outliers in numeric columns using Interquartile Range (IQR)."""

    def run(self, df: pd.DataFrame) -> dict:
        """Detect outliers per numeric column.

        Args:
            df: Input DataFrame.

        Returns:
            Dictionary mapping column names to outlier details.
        """
        print("[Outlier Detection Agent] Detecting outliers...")

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        outlier_report = {}

        for col in numeric_cols:
            series = df[col].dropna()
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = series[(series < lower_bound) | (series > upper_bound)]

            if len(outliers) > 0:
                outlier_report[col] = {
                    "count": int(len(outliers)),
                    "percentage": round(len(outliers) / len(series) * 100, 2),
                    "lower_bound": round(lower_bound, 4),
                    "upper_bound": round(upper_bound, 4),
                    "min_outlier": round(float(outliers.min()), 4),
                    "max_outlier": round(float(outliers.max()), 4),
                }

        total = sum(info["count"] for info in outlier_report.values())
        print(f"[Outlier Detection Agent] Found {total} outliers across {len(outlier_report)} columns")
        return outlier_report


def run(df) -> dict:
    """Module-level entry point — consistent with other agents."""
    agent = OutlierDetectionAgent()
    outlier_report = agent.run(df)
    total = sum(info["count"] for info in outlier_report.values())
    insights = []
    if outlier_report:
        insights.append(
            f"Detected {total} outlier(s) across {len(outlier_report)} column(s) using IQR method."
        )
        for col, info in outlier_report.items():
            if info["percentage"] > 5:
                insights.append(
                    f"Column '{col}' has {info['percentage']}% outliers "
                    f"(outside [{info['lower_bound']}, {info['upper_bound']}])."
                )
    else:
        insights.append("No significant outliers detected across numeric columns.")
    return {
        "summary": f"Outlier detection complete. {total} outlier(s) found.",
        "metrics": {"outlier_report": outlier_report, "total_outliers": total},
        "insights": insights,
    }
