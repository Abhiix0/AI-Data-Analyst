"""Data Loader Agent — detects file format and delegates to the correct loader."""

import os

import pandas as pd

from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle


class DataLoaderAgent:
    """Detects dataset format and loads it into a pandas DataFrame."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    def run(self, source: str) -> pd.DataFrame:
        """Load a dataset from a file path or Kaggle reference.

        Args:
            source: File path (CSV/Excel) or 'kaggle:<owner/dataset>' reference.

        Returns:
            pandas DataFrame.

        Raises:
            ValueError: If the file format is not supported.
            FileNotFoundError: If the file does not exist.
        """
        # Kaggle dataset
        if source.startswith("kaggle:"):
            dataset_ref = source.replace("kaggle:", "", 1)
            print(f"[Data Loader Agent] Fetching Kaggle dataset: {dataset_ref}")
            return load_kaggle(dataset_ref)

        # Local file
        if not os.path.isfile(source):
            raise FileNotFoundError(f"Dataset file not found: {source}")

        ext = os.path.splitext(source)[1].lower()

        if ext == ".csv":
            return load_csv(source)
        elif ext in (".xlsx", ".xls"):
            return load_excel(source)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported: {self.SUPPORTED_EXTENSIONS}"
            )
