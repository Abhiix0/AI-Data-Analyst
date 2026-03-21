"""Excel file loader for .xlsx and .xls files."""
from __future__ import annotations
import os
import pandas as pd


def load_excel(file_path: str) -> pd.DataFrame:
    """Load an Excel file into a DataFrame.

    Supports both .xlsx (openpyxl) and .xls (xlrd) formats.
    """
    ext = os.path.splitext(file_path)[1].lower()
    engine = "openpyxl" if ext == ".xlsx" else "xlrd"
    try:
        df = pd.read_excel(file_path, engine=engine)
    except Exception as e:
        raise ValueError(f"Could not read Excel file '{file_path}': {e}") from e
    print(f"[Excel Loader] Loaded {file_path} — {df.shape[0]} rows, {df.shape[1]} columns")
    return df
