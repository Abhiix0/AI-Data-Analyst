"""Anomaly Detection Agent — identifies anomalous records using IsolationForest.

Operates on numeric columns only and reports the proportion of records that
appear anomalous.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect anomalous rows using IsolationForest.

    Returns:
        {
            "summary": "Detected anomalous data points.",
            "metrics": {
                "anomaly_count": ...,
                "anomaly_percentage": ...
            },
            "insights": [
                "Approximately X% of records appear anomalous."
            ]
        }
    """
    numeric_df = df.select_dtypes(include="number").dropna()
    rows, cols = numeric_df.shape

    if rows < 20 or cols == 0:
        summary = "Not enough numeric data to perform anomaly detection."
        return {
            "summary": summary,
            "metrics": {"anomaly_count": 0, "anomaly_percentage": 0.0},
            "insights": [summary],
        }

    scaler = StandardScaler()
    X = scaler.fit_transform(numeric_df.values)

    model = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42,
    )
    model.fit(X)

    # Prediction: -1 = anomaly, 1 = normal
    preds = model.predict(X)
    anomaly_count = int((preds == -1).sum())
    anomaly_percentage = round(anomaly_count / rows * 100, 2)

    summary = "Detected anomalous data points using IsolationForest."
    insights = [
        f"Approximately {anomaly_percentage}% of records appear anomalous based on numeric features."
    ]

    return {
        "summary": summary,
        "metrics": {
            "anomaly_count": anomaly_count,
            "anomaly_percentage": anomaly_percentage,
        },
        "insights": insights,
    }

