"""Orchestrator V2 — new pipeline-based orchestration.

This is the refactored orchestrator using the new Pipeline architecture.
The old orchestrator.py is kept for backward compatibility.
"""

from __future__ import annotations

from typing import Dict, Any
import os
import pandas as pd

from pipeline import AnalysisPipeline
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent
from loaders.csv_loader import load_csv
from loaders.excel_loader import load_excel
from loaders.kaggle_loader import load_kaggle
from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def load_dataset(source: str) -> pd.DataFrame:
    """Load a dataset from various sources.
    
    Args:
        source: Dataset source (file path or kaggle:owner/dataset)
        
    Returns:
        Loaded DataFrame
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unsupported
    """
    # Kaggle dataset: format "kaggle:owner/dataset"
    if source.startswith("kaggle:"):
        dataset_ref = source.replace("kaggle:", "", 1)
        logger.info(f"Loading Kaggle dataset: {dataset_ref}")
        return load_kaggle(dataset_ref)

    if not os.path.isfile(source):
        raise FileNotFoundError(f"Dataset file not found: {source}")

    ext = os.path.splitext(source)[1].lower()
    logger.info(f"Loading local dataset: {source}")

    if ext == ".csv":
        return load_csv(source)
    if ext in (".xlsx", ".xls"):
        return load_excel(source)

    raise ValueError(
        f"Unsupported file format '{ext}'. "
        "Supported: .csv, .xlsx, .xls, or 'kaggle:<owner/dataset>'"
    )


def create_default_pipeline() -> AnalysisPipeline:
    """Create a pipeline with all default agents.
    
    Returns:
        Configured AnalysisPipeline
    """
    pipeline = AnalysisPipeline()
    
    # Import agents lazily to avoid circular imports
    from agents.dataset_understanding_agent import DatasetUnderstandingAgent
    from agents.clustering_agent import ClusteringAgent
    from agents.anomaly_detection_agent import AnomalyDetectionAgent
    from agents.feature_importance_agent import FeatureImportanceAgent
    from agents.insight_agent import InsightAgent
    
    # Add agents in pipeline order
    pipeline.add_agent(DatasetUnderstandingAgent())
    pipeline.add_agent(DataCleanerAgent())
    pipeline.add_agent(AnalysisAgent())
    pipeline.add_agent(ClusteringAgent())
    pipeline.add_agent(AnomalyDetectionAgent())
    pipeline.add_agent(FeatureImportanceAgent())
    pipeline.add_agent(InsightAgent())
    
    return pipeline


def run_pipeline(source: str) -> Dict[str, Any]:
    """Run the complete analysis pipeline on a dataset.
    
    Args:
        source: Dataset source (file path or kaggle:owner/dataset)
        
    Returns:
        Combined results from all agents
    """
    # Load dataset
    df = load_dataset(source)
    
    # Derive dataset name
    if source.startswith("kaggle:"):
        dataset_name = source.replace("kaggle:", "", 1)
    else:
        dataset_name = os.path.splitext(os.path.basename(source))[0]
    
    # Create and run pipeline
    pipeline = create_default_pipeline()
    result = pipeline.run(df, dataset_name=dataset_name)
    
    return result
