"""Integration tests for the complete analysis pipeline."""

from __future__ import annotations

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
from pipeline import AnalysisPipeline
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent


def test_basic_pipeline():
    """Test basic pipeline with minimal agents."""
    # Create test data
    df = pd.DataFrame({
        "age": [25, 30, 35, 40, 45],
        "salary": [50000, 60000, 70000, 80000, 90000],
        "department": ["Sales", "HR", "IT", "Sales", "IT"]
    })
    
    # Create pipeline
    pipeline = AnalysisPipeline()
    pipeline.add_agent(DataCleanerAgent())
    pipeline.add_agent(AnalysisAgent())
    
    # Run pipeline
    result = pipeline.run(df, dataset_name="test_data")
    
    # Verify results
    assert "summary" in result
    assert "metrics" in result
    assert "insights" in result
    assert len(result["insights"]) > 0
    
    print("✓ Basic pipeline test passed")


def test_csv_pipeline():
    """Test pipeline with CSV file."""
    from loaders.csv_loader import load_csv
    
    csv_path = os.path.join(os.path.dirname(__file__), "../data/test_data.csv")
    
    if not os.path.exists(csv_path):
        print(f"⚠ Skipping CSV test: {csv_path} not found")
        return
    
    df = load_csv(csv_path)
    
    pipeline = AnalysisPipeline()
    pipeline.add_agent(DataCleanerAgent())
    pipeline.add_agent(AnalysisAgent())
    
    result = pipeline.run(df, dataset_name="test_data")
    
    assert result is not None
    assert len(result["insights"]) > 0
    
    print("✓ CSV pipeline test passed")


def test_agent_enable_disable():
    """Test enabling and disabling agents."""
    df = pd.DataFrame({
        "x": [1, 2, 3],
        "y": [4, 5, 6]
    })
    
    pipeline = AnalysisPipeline()
    cleaner = DataCleanerAgent()
    analyst = AnalysisAgent()
    
    pipeline.add_agent(cleaner)
    pipeline.add_agent(analyst)
    
    # Disable analyst
    analyst.disable()
    
    result = pipeline.run(df)
    
    # Should only have cleaner results
    assert "DataCleanerAgent" in result["agent_results"]
    assert "AnalysisAgent" not in result["agent_results"]
    
    print("✓ Agent enable/disable test passed")


if __name__ == "__main__":
    test_basic_pipeline()
    test_csv_pipeline()
    test_agent_enable_disable()
    print("\n✓ All integration tests passed!")
