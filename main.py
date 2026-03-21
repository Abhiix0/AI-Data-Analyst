"""AI Data Analyst — Command Line Interface."""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from dotenv import load_dotenv
load_dotenv()

from orchestrator import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Data Analyst — Automated dataset analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py data/sales.csv
  python main.py data/report.xlsx
  python main.py kaggle:username/dataset-name
        """,
    )
    parser.add_argument(
        "source",
        help="Path to CSV/Excel file or kaggle:<owner/dataset>",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  AI Data Analyst")
    print("=" * 60)

    def progress(step, total, msg):
        bar = "#" * step + "-" * (total - step)
        print(f"\r[{bar}] {step}/{total} - {msg}", end="", flush=True)

    try:
        ctx = run_pipeline(args.source, progress_callback=progress)
        print("\n")
        print("=" * 60)
        print(f"  Dataset:         {ctx.file_name}")
        print(f"  Shape:           {ctx.shape_summary()}")
        print(f"  Insights:        {len(ctx.insights)}")
        print(f"  Recommendations: {len(ctx.recommendations)}")
        print(f"  Charts:          {len(ctx.chart_paths)}")
        if ctx.report_path:
            print(f"  Report:          {ctx.report_path}")
        if ctx.errors:
            print(f"\n  Warnings: {len(ctx.errors)}")
            for err in ctx.errors:
                print(f"    - {err}")
        print("=" * 60)
        print("\nRun the dashboard: streamlit run dashboard.py\n")
    except (FileNotFoundError, ValueError) as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
