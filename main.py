from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from dotenv import load_dotenv
load_dotenv()

from orchestrator import run_pipeline, _load_dataset
from agents.query_agent import answer_query


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Data Analyst")
    parser.add_argument("source", help="Path to CSV/Excel or kaggle:<owner/dataset>")
    args = parser.parse_args()

    try:
        result = run_pipeline(args.source)
        print(f"\nInsights: {len(result['insights'])}")
        print(f"Recommendations: {len(result['recommendations'])}")
        print(f"Charts: {len(result['chart_paths'])}")
        print(f"Report: {result['report_path']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
