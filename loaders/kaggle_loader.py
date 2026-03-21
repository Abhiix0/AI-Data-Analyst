"""Kaggle dataset downloader and loader."""
from __future__ import annotations
import os
import glob
import subprocess

import pandas as pd
from loaders.csv_loader import load_csv


DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kaggle_downloads")


def load_kaggle(dataset_ref: str) -> pd.DataFrame:
    """Download a Kaggle dataset and return the first CSV as a DataFrame.

    Args:
        dataset_ref: Kaggle dataset reference, e.g. 'username/dataset-name'.

    Returns:
        pandas DataFrame with the loaded data.

    Raises:
        ValueError: Authentication failure, dataset not found, or network error.
        FileNotFoundError: No CSV found after extraction.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    existing_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "**", "*.csv"), recursive=True))

    print(f"[Kaggle Loader] Downloading {dataset_ref}...")
    try:
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d", dataset_ref, "-p", DOWNLOAD_DIR, "--unzip"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Network error while fetching from Kaggle. Check your connection.")
    except FileNotFoundError:
        raise ValueError(
            "Kaggle CLI not found. Install it with: pip install kaggle"
        )

    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    combined = (stderr + " " + stdout).lower()

    if result.returncode != 0:
        if any(k in combined for k in ["401", "unauthorized", "authentication", "api key", "credentials"]):
            raise ValueError(
                "Kaggle authentication failed. Check your KAGGLE_USERNAME and KAGGLE_KEY in .env"
            )
        if any(k in combined for k in ["404", "not found", "no such dataset", "dataset not found"]):
            raise ValueError(
                f"Dataset '{dataset_ref}' not found on Kaggle."
            )
        if any(k in combined for k in ["connection", "network", "timeout", "ssl", "socket"]):
            raise ValueError(
                "Network error while fetching from Kaggle. Check your connection."
            )
        raise ValueError(f"Kaggle download failed: {stderr or stdout}")

    all_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "**", "*.csv"), recursive=True))
    new_files = list(all_files - existing_files)

    if not new_files:
        csv_files = list(all_files)
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in downloaded dataset '{dataset_ref}'.")
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        csv_path = csv_files[0]
    else:
        csv_path = new_files[0]

    return load_csv(csv_path)
