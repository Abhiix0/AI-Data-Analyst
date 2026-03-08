"""Feature Importance Agent — identifies predictive features using RandomForest.

This agent attempts to detect a plausible target column and then uses a
RandomForestClassifier on numeric features to estimate feature importances.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


def _guess_target_column(df: pd.DataFrame, dataset_context: Optional[Dict[str, Any]]) -> Optional[str]:
    """Heuristically guess a target column name.

    Preference order:
    1. If dataset_context insights mention 'Possible target variable: <col>' use that.
    2. Columns named like 'target', 'label', 'churn', 'default' (case-insensitive).
    3. Any binary or low-cardinality categorical column.
    """
    if dataset_context:
        for text in dataset_context.get("insights", []):
            lower = str(text).lower()
            key = "possible target variable:"
            if key in lower:
                after = lower.split(key, 1)[1].strip()
                # crude extraction of column name between quotes if present
                for col in df.columns:
                    if col.lower() in after:
                        return col

    lower_cols = {c.lower(): c for c in df.columns}
    for candidate in ["target", "label", "churn", "default"]:
        if candidate in lower_cols:
            return lower_cols[candidate]

    # Fallback: choose a low-cardinality categorical/binary column
    for col in df.columns:
        series = df[col]
        if series.dtype == "object" or str(series.dtype).startswith("category"):
            unique_vals = series.dropna().nunique()
            if 2 <= unique_vals <= 10:
                return col

    return None


def run(df: pd.DataFrame, dataset_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Estimate feature importances with a RandomForestClassifier.

    Returns:
        {
            "summary": "Identified important predictive features.",
            "metrics": {
                "top_features": {...}
            },
            "insights": [
                "Feature X appears to strongly influence the target variable."
            ]
        }
    """
    target_col = _guess_target_column(df, dataset_context)

    if target_col is None:
        summary = "Could not identify a suitable target column for feature importance analysis."
        return {
            "summary": summary,
            "metrics": {"top_features": {}},
            "insights": [summary],
        }

    y_raw = df[target_col].dropna()
    if y_raw.nunique() < 2:
        summary = f"Target column '{target_col}' does not have at least two distinct classes."
        return {
            "summary": summary,
            "metrics": {"top_features": {}},
            "insights": [summary],
        }

    # Align X with y index and restrict to numeric columns only.
    numeric_df = df.select_dtypes(include="number")
    X = numeric_df.loc[y_raw.index]

    if X.shape[1] == 0 or X.shape[0] < 30:
        summary = "Not enough numeric features or rows to compute stable feature importances."
        return {
            "summary": summary,
            "metrics": {"top_features": {}},
            "insights": [summary],
        }

    # Encode target if not already numeric.
    if not pd.api.types.is_numeric_dtype(y_raw):
        encoder = LabelEncoder()
        y = encoder.fit_transform(y_raw.astype(str))
    else:
        y = y_raw.values

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    importances = model.feature_importances_
    feature_names: List[str] = list(X.columns)
    scores = sorted(
        zip(feature_names, importances),
        key=lambda kv: kv[1],
        reverse=True,
    )

    top_n = 5
    top_features = {name: round(float(score), 4) for name, score in scores[:top_n]}

    summary = f"Identified important predictive features for target '{target_col}'."

    insights: List[str] = []
    if top_features:
        insights.append(
            f"Top predictive features for '{target_col}' include: "
            + ", ".join(top_features.keys())
            + "."
        )
        # Highlight the single strongest feature
        strongest = next(iter(top_features.items()))
        insights.append(
            f"Feature '{strongest[0]}' appears to strongly influence the target variable."
        )
    else:
        insights.append("Feature importances could not be reliably estimated.")

    return {
        "summary": summary,
        "metrics": {"top_features": top_features},
        "insights": insights,
    }

