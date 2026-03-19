"""Test script for LLM-powered Insight Agent."""

import pandas as pd
from agents.profiling_agent import ProfilingAgent
from agents.pattern_detection_agent import PatternDetectionAgent
from agents.outlier_detection_agent import OutlierDetectionAgent
from agents.insight_agent import InsightAgent


def test_llm_insight_agent():
    """Test the LLM Insight Agent with a sample dataset."""
    
    print("=" * 70)
    print("  Testing LLM-Powered Insight Agent")
    print("=" * 70)
    print()
    
    # Create a small test dataset
    data = {
        'age': [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
        'salary': [50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000, 130000, 140000],
        'department': ['Sales', 'Engineering', 'Sales', 'HR', 'Engineering', 
                      'Sales', 'HR', 'Engineering', 'Sales', 'HR'],
        'performance': [3.5, 4.2, 3.8, 4.5, 4.0, 3.9, 4.3, 4.1, 3.7, 4.4]
    }
    df = pd.DataFrame(data)
    
    print("Sample Dataset:")
    print(df.head())
    print()
    
    # Step 1: Profile the dataset
    print("Step 1: Profiling dataset...")
    profiler = ProfilingAgent()
    profile = profiler.run(df)
    print()
    
    # Step 2: Detect patterns
    print("Step 2: Detecting patterns...")
    pattern_detector = PatternDetectionAgent()
    patterns = pattern_detector.run(df)
    print()
    
    # Step 3: Detect outliers
    print("Step 3: Detecting outliers...")
    outlier_detector = OutlierDetectionAgent()
    outliers = outlier_detector.run(df)
    print()
    
    # Step 4: Generate LLM-powered insights
    print("Step 4: Generating LLM-powered insights...")
    print("-" * 70)
    insight_agent = InsightAgent(model="llama3", use_llm=True)
    insights = insight_agent.run(df, profile, patterns, outliers)
    print()
    
    # Display insights
    print("=" * 70)
    print("  LLM-Generated Insights")
    print("=" * 70)
    print()
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
        print()
    
    print("=" * 70)
    print("  Test Complete!")
    print("=" * 70)
    print()
    print(f"✅ Generated {len(insights)} professional insights using llama3")
    print()


if __name__ == "__main__":
    test_llm_insight_agent()
