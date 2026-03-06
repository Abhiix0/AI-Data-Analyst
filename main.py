"""AI Data Analyst Assistant — CLI entry point."""

import argparse
import sys
import os

# Ensure project root is on the path so imports work when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="AI Data Analyst Assistant — Automated dataset analysis, visualization, and reporting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python main.py --source data.csv
  python main.py --source report.xlsx
  python main.py --source kaggle:username/dataset-name
        """,
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to a CSV/Excel file, or 'kaggle:<owner/dataset>' to fetch from Kaggle.",
    )

    args = parser.parse_args()

    try:
        orchestrator = Orchestrator()
        report_path = orchestrator.run_pipeline(args.source)
        print(f"\nDone! Open your report at:\n  {report_path}")
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
