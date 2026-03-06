"""Profiling Agent — analyzes dataset structure and metadata."""

import pandas as pd


class ProfilingAgent:
    """Generates a comprehensive profile of the dataset."""

    def run(self, df: pd.DataFrame) -> dict:
        """Profile the dataset.

        Args:
            df: Input DataFrame.

        Returns:
            Dictionary containing profiling results.
        """
        print("[Profiling Agent] Profiling dataset...")

        profile = {
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_stats": {},
            "categorical_summary": {},
        }

        # Numeric column statistics
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            profile["numeric_stats"] = df[numeric_cols].describe().to_dict()

        # Categorical column summaries
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cat_cols:
            profile["categorical_summary"][col] = {
                "unique_values": int(df[col].nunique()),
                "top_values": df[col].value_counts().head(5).to_dict(),
            }

        print(
            f"[Profiling Agent] Done — {profile['shape']['rows']} rows, "
            f"{profile['shape']['columns']} columns, "
            f"{profile['duplicate_rows']} duplicates"
        )
        return profile
