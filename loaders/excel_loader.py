"""Excel file loader for .xlsx and .xls files."""

import pandas as pd


def load_excel(file_path: str) -> pd.DataFrame:
    """Load an Excel file into a DataFrame.

    Args:
        file_path: Path to the Excel file (.xlsx or .xls).

    Returns:
        pandas DataFrame with the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed.
    """
    df = pd.read_excel(file_path, engine="openpyxl")
    return df
