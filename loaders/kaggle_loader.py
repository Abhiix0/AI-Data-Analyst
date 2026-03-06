"""Kaggle dataset downloader and loader."""

import os
import subprocess
import zipfile
import glob

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
        RuntimeError: If the download or extraction fails.
        FileNotFoundError: If no CSV file is found after extraction.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Get list of existing files before download
    existing_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "**", "*.csv"), recursive=True))

    print(f"[Kaggle Loader] Downloading {dataset_ref}...")
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset_ref, "-p", DOWNLOAD_DIR, "--unzip"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Kaggle download failed: {result.stderr.strip()}")

    # Find newly downloaded CSV files
    all_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "**", "*.csv"), recursive=True))
    new_files = list(all_files - existing_files)
    
    # If no new files, try to find the most recently modified CSV
    if not new_files:
        csv_files = list(all_files)
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in downloaded dataset {dataset_ref}")
        # Sort by modification time, newest first
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        csv_path = csv_files[0]
        print(f"[Kaggle Loader] Using most recent file: {csv_path}")
    else:
        csv_path = new_files[0]
        print(f"[Kaggle Loader] Using newly downloaded: {csv_path}")
    
    # Use csv_loader for better type conversion
    df = load_csv(csv_path)
    return df
