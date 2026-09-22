"""Kaggle dataset downloader and loader into Polars DataFrames."""
from __future__ import annotations
import glob
import os
import subprocess
from typing import Optional
import polars as pl
from packages.ingestion.csv_loader import load_csv
from packages.ingestion.errors import (
    KaggleAuthError,
    KaggleNotFoundError,
    KaggleNetworkError,
    IngestionError,
)

DEFAULT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "data", "kaggle_downloads")


def load_kaggle(dataset_ref: str, download_dir: Optional[str] = None) -> pl.DataFrame:
    """Download a Kaggle dataset via CLI and return the first CSV as a Polars DataFrame.

    Args:
        dataset_ref: Kaggle dataset reference, e.g. 'username/dataset-name'.
        download_dir: Target directory for downloading archive.

    Returns:
        polars.DataFrame

    Raises:
        KaggleAuthError: Authentication failure.
        KaggleNotFoundError: Dataset does not exist.
        KaggleNetworkError: Network or timeout error.
        IngestionError: Other CLI failures.
    """
    target_dir = download_dir or DEFAULT_DOWNLOAD_DIR
    os.makedirs(target_dir, exist_ok=True)

    existing_files = set(glob.glob(os.path.join(target_dir, "**", "*.csv"), recursive=True))

    try:
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d", dataset_ref, "-p", target_dir, "--unzip"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        raise KaggleNetworkError("Network timeout while downloading dataset from Kaggle.") from e
    except FileNotFoundError as e:
        raise IngestionError("Kaggle CLI not installed or not found on PATH.") from e

    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    combined = (stderr + " " + stdout).lower()

    if result.returncode != 0:
        classify_kaggle_error(combined, dataset_ref, stderr or stdout)

    all_files = set(glob.glob(os.path.join(target_dir, "**", "*.csv"), recursive=True))
    new_files = list(all_files - existing_files)

    if not new_files:
        csv_files = list(all_files)
        if not csv_files:
            raise IngestionError(f"No CSV files found in downloaded Kaggle dataset '{dataset_ref}'.")
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        csv_path = csv_files[0]
    else:
        csv_path = new_files[0]

    return load_csv(csv_path)


def classify_kaggle_error(combined_output: str, dataset_ref: str, raw_msg: str) -> None:
    """Classify Kaggle CLI error output into specific typed exceptions."""
    if any(k in combined_output for k in ["401", "unauthorized", "authentication", "api key", "credentials"]):
        raise KaggleAuthError("Kaggle authentication failed. Check your credentials.")
    if any(k in combined_output for k in ["404", "not found", "no such dataset", "dataset not found"]):
        raise KaggleNotFoundError(f"Dataset '{dataset_ref}' not found on Kaggle.")
    if any(k in combined_output for k in ["connection", "network", "timeout", "ssl", "socket"]):
        raise KaggleNetworkError("Network error while connecting to Kaggle.")
    raise IngestionError(f"Kaggle download failed: {raw_msg}")
