"""File utilities for data loading and saving.

Provides helper functions for file operations and path management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def ensure_directory(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_extension(filepath: str) -> str:
    """Get file extension in lowercase.
    
    Args:
        filepath: Path to file
        
    Returns:
        File extension (e.g., '.csv', '.xlsx')
    """
    return os.path.splitext(filepath)[1].lower()


def is_csv_file(filepath: str) -> bool:
    """Check if file is a CSV file.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if CSV file
    """
    return get_file_extension(filepath) == ".csv"


def is_excel_file(filepath: str) -> bool:
    """Check if file is an Excel file.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if Excel file
    """
    return get_file_extension(filepath) in [".xlsx", ".xls"]


def get_output_path(
    filename: str,
    output_dir: str = "outputs",
    subdir: Optional[str] = None
) -> Path:
    """Get path for output file, ensuring directory exists.
    
    Args:
        filename: Output filename
        output_dir: Base output directory
        subdir: Optional subdirectory within output_dir
        
    Returns:
        Path object for output file
    """
    if subdir:
        full_dir = os.path.join(output_dir, subdir)
    else:
        full_dir = output_dir
    
    ensure_directory(full_dir)
    return Path(full_dir) / filename


def file_exists(filepath: str) -> bool:
    """Check if file exists.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if file exists
    """
    return os.path.isfile(filepath)


def get_file_size(filepath: str) -> int:
    """Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    return os.path.getsize(filepath)
