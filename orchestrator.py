"""Orchestrator — coordinates the multi-agent analysis pipeline."""

from agents.data_loader_agent import DataLoaderAgent
from agents.profiling_agent import ProfilingAgent
from agents.visualization_agent import VisualizationAgent
from agents.pattern_detection_agent import PatternDetectionAgent
from agents.outlier_detection_agent import OutlierDetectionAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent
from agents.report_agent import ReportAgent


class Orchestrator:
    """Runs the full analysis pipeline by calling each agent in sequence."""

    def __init__(self):
        self.data_loader = DataLoaderAgent()
        self.profiler = ProfilingAgent()
        self.visualizer = VisualizationAgent()
        self.pattern_detector = PatternDetectionAgent()
        self.outlier_detector = OutlierDetectionAgent()
        self.insight_engine = InsightAgent()
        self.recommender = RecommendationAgent()
        self.reporter = ReportAgent()

    def run_pipeline(self, source: str) -> str:
        """Execute the complete analysis pipeline.

        Args:
            source: File path (CSV/Excel) or 'kaggle:<owner/dataset>' reference.

        Returns:
            Path to the generated report.
        """
        print("=" * 60)
        print("  AI Data Analyst Assistant — Starting Analysis Pipeline")
        print("=" * 60)
        print()

        # Step 1: Load data
        df = self.data_loader.run(source)
        print()

        # Step 2: Profile dataset
        profile = self.profiler.run(df)
        print()

        # Step 3: Generate visualizations
        charts = self.visualizer.run(df)
        print()

        # Step 4: Detect patterns
        patterns = self.pattern_detector.run(df)
        print()

        # Step 5: Detect outliers
        outliers = self.outlier_detector.run(df)
        print()

        # Step 6: Generate insights
        insights = self.insight_engine.run(df, profile, patterns, outliers)
        print()

        # Step 7: Generate recommendations
        recommendations = self.recommender.run(profile, patterns, outliers, insights)
        print()

        # Step 8: Compile report
        report_path = self.reporter.run(
            source=source,
            profile=profile,
            charts=charts,
            patterns=patterns,
            outliers=outliers,
            insights=insights,
            recommendations=recommendations,
        )

        print()
        print("=" * 60)
        print("  ✅ Analysis Complete!")
        print(f"  📄 Report: {report_path}")
        print(f"  📊 Charts: {len(charts)} saved to outputs/charts/")
        print("=" * 60)

        return report_path
