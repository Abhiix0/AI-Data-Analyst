"""CSV file loader with encoding and delimiter auto-detection."""

import pandas as pd


def load_csv(file_path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Attempts UTF-8 first, falls back to latin-1.
    Tries comma delimiter, then semicolon.
    Attempts to convert string columns to numeric if possible.

    Args:
        file_path: Path to the CSV file.

    Returns:
        pandas DataFrame with the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    encodings = ["utf-8", "latin-1"]
    delimiters = [",", ";", "\t"]

    for encoding in encodings:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                if len(df.columns) > 1:
                    # Try to convert string columns to numeric
                    df = _auto_convert_types(df)
                    return df
            except Exception:
                continue

    # Final fallback — let pandas figure it out
    df = pd.read_csv(file_path)
    df = _auto_convert_types(df)
    return df


def _auto_convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to convert string columns to numeric types.
    
    Handles common issues like whitespace, empty strings, etc.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with converted types where possible
    """
    for col in df.columns:
        # Check if column is string/object type
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
            # Try to convert to numeric
            # First strip whitespace and replace empty strings with NaN
            cleaned = df[col].astype(str).str.strip()
            cleaned = cleaned.replace(['', 'nan', 'None'], pd.NA)
            
            # Try numeric conversion
            numeric_col = pd.to_numeric(cleaned, errors='coerce')
            
            # If more than 50% of non-null values converted successfully, use numeric
            non_null_original = df[col].notna().sum()
            non_null_converted = numeric_col.notna().sum()
            
            if non_null_original > 0 and (non_null_converted / non_null_original) > 0.5:
                df[col] = numeric_col
                
    return df
