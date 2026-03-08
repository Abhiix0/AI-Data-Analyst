"""AI Data Analyst — Phase 1 CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure project root is on the path so imports work when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_pipeline, _load_dataset
from agents import query_agent


def main() -> None:
    """Parse CLI arguments, run the orchestrator, and enter Q&A mode."""
    parser = argparse.ArgumentParser(
        description="AI Data Analyst — minimal Phase 1 pipeline (cleaning, analysis, insights).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python main.py data.csv
  python main.py report.xlsx
  python main.py kaggle:username/dataset-name
        """,
    )
    parser.add_argument(
        "source",
        help="Path to a CSV/Excel file, or 'kaggle:<owner/dataset>' to fetch from Kaggle.",
    )

    args = parser.parse_args()

    try:
        # Run the analysis pipeline once to produce a structured report,
        # including dataset context from the understanding agent.
        report = run_pipeline(args.source)

        print("\nInitial structured report:\n")
        print(json.dumps(report, indent=2, ensure_ascii=False))

        # Load the DataFrame for interactive queries.
        df = _load_dataset(args.source)
        dataset_context = report.get("dataset_context")

        # Interactive question-answering loop.
        print("\nEnter natural language questions about the dataset.")
        print("Type 'exit', 'quit', or press Ctrl+C to leave.\n")

        while True:
            try:
                question = input("ask> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not question:
                continue
            if question.lower() in {"exit", "quit", "q"}:
                print("Goodbye.")
                break

            answer = query_agent.answer_query(df, question, dataset_context)

            print("\nAnswer:")
            print(answer.get("summary", "No answer available."))

            insights = answer.get("insights") or []
            if insights:
                print("\nDetails:")
                for item in insights:
                    print(f"- {item}")
            print()

    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:  # pragma: no cover - defensive catch-all
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

