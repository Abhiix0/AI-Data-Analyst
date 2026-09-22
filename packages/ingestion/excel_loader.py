"""Excel file loader for .xlsx and .xls formats into Polars DataFrames."""
from __future__ import annotations
import io
import os
from typing import Union
import polars as pl
from packages.ingestion.errors import IngestionFormatError


def load_excel(source: Union[str, bytes, io.BytesIO], filename_hint: str = "") -> pl.DataFrame:
    """Load an Excel workbook into a Polars DataFrame.

    Supports .xlsx and .xls formats.

    Args:
        source: File path, bytes, or BytesIO buffer.
        filename_hint: Optional filename for extension inspection.

    Returns:
        polars.DataFrame
    """
    try:
        if isinstance(source, str):
            if not os.path.isfile(source):
                raise FileNotFoundError(f"Excel file not found: {source}")
            ext = os.path.splitext(source)[1].lower()
            engine = "openpyxl" if ext == ".xlsx" else "calamine"
            try:
                return pl.read_excel(source, engine=engine)
            except Exception:
                # Fallback via pandas read_excel if polars engine needs help
                import pandas as pd
                pd_engine = "openpyxl" if ext == ".xlsx" else "xlrd"
                pdf = pd.read_excel(source, engine=pd_engine)
                return pl.from_pandas(pdf)
        else:
            raw_bytes = source.getvalue() if isinstance(source, io.BytesIO) else source
            try:
                return pl.read_excel(io.BytesIO(raw_bytes))
            except Exception:
                import pandas as pd
                ext = os.path.splitext(filename_hint)[1].lower()
                pd_engine = "openpyxl" if ext == ".xlsx" else "xlrd"
                pdf = pd.read_excel(io.BytesIO(raw_bytes), engine=pd_engine)
                return pl.from_pandas(pdf)
    except Exception as e:
        raise IngestionFormatError(f"Could not read Excel file: {e}") from e
