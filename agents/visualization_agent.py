"""Visualization Agent — generates smart charts based on profile findings."""
from __future__ import annotations
from typing import Dict, Any, List
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "charts")


def _clear_charts_dir():
    """Remove old charts before generating new ones."""
    os.makedirs(CHARTS_DIR, exist_ok=True)
    for f in os.listdir(CHARTS_DIR):
        if f.endswith(".png"):
            os.remove(os.path.join(CHARTS_DIR, f))


def run(df: pd.DataFrame, profile: Dict[str, Any]) -> List[str]:
    """Generate charts intelligently based on what the profile found.
    Returns list of saved chart paths."""
    if df.empty or len(df.columns) == 0:
        return []
    _clear_charts_dir()
    sns.set_theme(style="whitegrid", palette="husl")
    saved: List[str] = []

    numeric_stats = profile.get("numeric_stats", {})
    outliers = profile.get("outliers", {})
    top_correlations = profile.get("top_correlations", [])
    categorical_stats = profile.get("categorical_stats", {})

    numeric_cols = list(numeric_stats.keys())
    cat_cols = list(categorical_stats.keys())

    # 1. Histograms — prioritize skewed or outlier-prone columns
    priority_numeric = sorted(
        numeric_cols,
        key=lambda c: (c in outliers, abs(numeric_stats[c].get("skew", 0))),
        reverse=True,
    )
    for col in priority_numeric[:6]:
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            df[col].dropna().hist(bins=30, ax=ax, color="#5A9BD5", edgecolor="white")
            ax.set_title(f"Distribution: {col}", fontsize=13, fontweight="bold")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")
            path = os.path.join(CHARTS_DIR, f"hist_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            saved.append(path)
        except Exception:
            plt.close("all")

    # 2. Box plots — only for columns that actually have outliers
    outlier_cols = list(outliers.keys())[:4]
    for col in outlier_cols:
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.boxplot(y=df[col].dropna(), ax=ax, color="#70AD47")
            ax.set_title(f"Outliers: {col}", fontsize=13, fontweight="bold")
            path = os.path.join(CHARTS_DIR, f"box_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            saved.append(path)
        except Exception:
            plt.close("all")

    # 3. Scatter plots — top 3 strongly correlated pairs
    strong_pairs = [c for c in top_correlations if abs(c["r"]) >= 0.5][:3]
    for pair in strong_pairs:
        col_a, col_b = pair["col_a"], pair["col_b"]
        if col_a not in df.columns or col_b not in df.columns:
            continue
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.scatter(df[col_a], df[col_b], alpha=0.4, color="#E05C5C", s=15)
            ax.set_xlabel(col_a)
            ax.set_ylabel(col_b)
            ax.set_title(f"Correlation: {col_a} vs {col_b} (r={pair['r']})", fontsize=13, fontweight="bold")
            path = os.path.join(CHARTS_DIR, f"scatter_{col_a}_vs_{col_b}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            saved.append(path)
        except Exception:
            plt.close("all")

    # 4. Correlation heatmap
    if len(numeric_cols) >= 2:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            corr = df[numeric_cols].corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                        ax=ax, linewidths=0.5, square=True)
            ax.set_title("Correlation Heatmap", fontsize=13, fontweight="bold")
            path = os.path.join(CHARTS_DIR, "correlation_heatmap.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            saved.append(path)
        except Exception:
            plt.close("all")

    # 5. Bar charts — categorical columns with 2-20 unique values
    useful_cat = [c for c in cat_cols if 2 <= categorical_stats[c]["unique_count"] <= 20][:4]
    for col in useful_cat:
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            counts = df[col].value_counts().head(15)
            counts.plot(kind="bar", ax=ax, color="#ED7D31", edgecolor="white")
            ax.set_title(f"Value Counts: {col}", fontsize=13, fontweight="bold")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            path = os.path.join(CHARTS_DIR, f"bar_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            saved.append(path)
        except Exception:
            plt.close("all")

    return saved
