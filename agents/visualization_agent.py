"""Visualization Agent — generates charts for numeric and categorical data."""

import os

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "charts")


class VisualizationAgent:
    """Automatically generates and saves visualizations."""

    def __init__(self):
        os.makedirs(CHARTS_DIR, exist_ok=True)
        sns.set_theme(style="whitegrid", palette="husl")

    def run(self, df: pd.DataFrame) -> list[str]:
        """Generate charts and return list of saved file paths.

        Args:
            df: Input DataFrame.

        Returns:
            List of paths to saved chart images.
        """
        print("[Visualization Agent] Generating charts...")
        saved = []

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # 1. Histograms for numeric columns
        if numeric_cols:
            saved.extend(self._histograms(df, numeric_cols))

        # 2. Box plots for numeric columns
        if numeric_cols:
            saved.extend(self._boxplots(df, numeric_cols))

        # 3. Correlation heatmap
        if len(numeric_cols) >= 2:
            saved.append(self._correlation_heatmap(df, numeric_cols))

        # 4. Bar charts for categorical columns
        if cat_cols:
            saved.extend(self._bar_charts(df, cat_cols))

        print(f"[Visualization Agent] Saved {len(saved)} charts to {CHARTS_DIR}")
        return saved

    # ── Chart generators ──────────────────────────────────────────

    def _histograms(self, df: pd.DataFrame, cols: list[str]) -> list[str]:
        paths = []
        for col in cols[:6]:  # Limit to 6 columns
            fig, ax = plt.subplots(figsize=(8, 5))
            df[col].dropna().hist(bins=30, ax=ax, color="#5A9BD5", edgecolor="white")
            ax.set_title(f"Distribution of {col}", fontsize=14, fontweight="bold")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")
            path = os.path.join(CHARTS_DIR, f"hist_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            paths.append(path)
        return paths

    def _boxplots(self, df: pd.DataFrame, cols: list[str]) -> list[str]:
        paths = []
        for col in cols[:6]:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.boxplot(y=df[col].dropna(), ax=ax, color="#70AD47")
            ax.set_title(f"Box Plot of {col}", fontsize=14, fontweight="bold")
            path = os.path.join(CHARTS_DIR, f"box_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            paths.append(path)
        return paths

    def _correlation_heatmap(self, df: pd.DataFrame, cols: list[str]) -> str:
        fig, ax = plt.subplots(figsize=(10, 8))
        corr = df[cols].corr()
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax,
                    linewidths=0.5, square=True)
        ax.set_title("Correlation Heatmap", fontsize=14, fontweight="bold")
        path = os.path.join(CHARTS_DIR, "correlation_heatmap.png")
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return path

    def _bar_charts(self, df: pd.DataFrame, cols: list[str]) -> list[str]:
        paths = []
        for col in cols[:4]:  # Limit to 4 categorical columns
            fig, ax = plt.subplots(figsize=(8, 5))
            counts = df[col].value_counts().head(10)
            counts.plot(kind="bar", ax=ax, color="#ED7D31", edgecolor="white")
            ax.set_title(f"Top Values in {col}", fontsize=14, fontweight="bold")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            path = os.path.join(CHARTS_DIR, f"bar_{col}.png")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            paths.append(path)
        return paths


def run(df) -> dict:
    """Module-level entry point — consistent with other agents."""
    agent = VisualizationAgent()
    chart_paths = agent.run(df)
    return {
        "summary": f"Generated {len(chart_paths)} chart(s).",
        "metrics": {"chart_count": len(chart_paths), "chart_paths": chart_paths},
        "insights": [f"Saved {len(chart_paths)} visualization(s) to outputs/charts/."],
        "chart_paths": chart_paths,
    }
