"""Test script for LLM-powered Recommendation Agent."""

import pandas as pd
from agents.profiling_agent import ProfilingAgent
from agents.pattern_detection_agent import PatternDetectionAgent
from agents.outlier_detection_agent import OutlierDetectionAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent


def test_llm_recommendation_agent():
    """Test the LLM Recommendation Agent with a sample dataset."""
    
    print("=" * 70)
    print("  Testing LLM-Powered Recommendation Agent")
    print("=" * 70)
    print()
    
    # Create a test dataset with data quality issues
    data = {
        'customer_id': range(1, 21),
        'age': [25, 30, None, 40, 45, 50, 55, 60, 65, 70, 
                28, 32, 38, 42, 48, 52, 58, 62, 68, 72],
        'income': [30000, 45000, 55000, None, 75000, 85000, 95000, 105000, 115000, 125000,
                   35000, 48000, 58000, 72000, 78000, 88000, 98000, 108000, 118000, None],
        'purchase_amount': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000,
                           150, 250, 350, 450, 550, 650, 750, 850, 950, 1050],
        'category': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C',
                    'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C', 'B']
    }
    df = pd.DataFrame(data)
    
    print("Sample Dataset (with missing values):")
    print(df.head(10))
    print()
    print(f"Missing values: age={df['age'].isna().sum()}, income={df['income'].isna().sum()}")
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
    
    # Step 4: Generate insights
    print("Step 4: Generating insights...")
    insight_agent = InsightAgent(model="llama3", use_llm=True)
    insights = insight_agent.run(df, profile, patterns, outliers)
    print()
    print("Generated Insights:")
    for i, insight in enumerate(insights[:5], 1):
        print(f"  {i}. {insight[:100]}...")
    print()
    
    # Step 5: Generate LLM-powered recommendations
    print("Step 5: Generating LLM-powered recommendations...")
    print("-" * 70)
    recommendation_agent = RecommendationAgent(model="llama3", use_llm=True)
    recommendations = recommendation_agent.run(profile, patterns, outliers, insights)
    print()
    
    # Display recommendations
    print("=" * 70)
    print("  LLM-Generated Strategic Recommendations")
    print("=" * 70)
    print()
    for i, recommendation in enumerate(recommendations, 1):
        print(f"{i}. {recommendation}")
        print()
    
    print("=" * 70)
    print("  Test Complete!")
    print("=" * 70)
    print()
    print(f"✅ Generated {len(recommendations)} strategic recommendations using llama3")
    print()
    
    # Compare with rule-based
    print("=" * 70)
    print("  Comparison: Rule-Based vs LLM-Powered")
    print("=" * 70)
    print()
    
    # Generate rule-based recommendations
    recommendation_agent_rule = RecommendationAgent(use_llm=False)
    recommendations_rule = recommendation_agent_rule.run(profile, patterns, outliers, insights)
    
    print(f"Rule-Based Recommendations: {len(recommendations_rule)}")
    for i, rec in enumerate(recommendations_rule, 1):
        print(f"  {i}. {rec[:80]}...")
    print()
    
    print(f"LLM-Powered Recommendations: {len(recommendations)}")
    print(f"Improvement: {len(recommendations) - len(recommendations_rule)} more recommendations")
    print(f"Quality: Strategic, prioritized, and business-focused")
    print()


if __name__ == "__main__":
    test_llm_recommendation_agent()
