"""Clustering Agent — detects natural groups in the dataset.

Uses KMeans on numeric columns only to find coarse clusters and reports
cluster sizes. This agent does not mutate the original DataFrame.
"""

from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect clusters in the dataset using KMeans.

    Returns:
        {
            "summary": "Detected natural groups in the dataset.",
            "metrics": {
                "cluster_count": ...,
                "cluster_sizes": {...}
            },
            "insights": [
                "Dataset appears to contain X natural clusters.",
                "Cluster 0 contains ... records."
            ]
        }
    """
    numeric_df = df.select_dtypes(include="number").dropna()
    rows, cols = numeric_df.shape

    if rows < 20 or cols == 0:
        summary = "Not enough numeric data to perform reliable clustering."
        return {
            "summary": summary,
            "metrics": {"cluster_count": 0, "cluster_sizes": {}},
            "insights": [summary],
        }

    # Choose a small number of clusters based on data size.
    if rows < 50:
        n_clusters = 3
    elif rows < 200:
        n_clusters = 4
    else:
        n_clusters = 5

    # Normalize numeric features for KMeans.
    scaler = StandardScaler()
    X = scaler.fit_transform(numeric_df.values)

    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X)

    unique, counts = np.unique(labels, return_counts=True)
    cluster_sizes = {int(k): int(v) for k, v in zip(unique, counts)}

    summary = "Detected natural groups in the dataset using KMeans clustering."

    insights = [
        f"Dataset appears to contain {len(cluster_sizes)} natural clusters based on numeric features."
    ]
    for cluster_id, size in cluster_sizes.items():
        insights.append(f"Cluster {cluster_id} contains {size} records.")

    return {
        "summary": summary,
        "metrics": {
            "cluster_count": len(cluster_sizes),
            "cluster_sizes": cluster_sizes,
        },
        "insights": insights,
    }

