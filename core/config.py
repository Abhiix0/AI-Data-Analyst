"""Shared project configuration and path constants."""
from __future__ import annotations
import os

# Absolute path to the project root (parent of this file's directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHARTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "charts")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")
