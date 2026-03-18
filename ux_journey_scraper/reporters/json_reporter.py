"""
JSON reporter for journey analysis results.
"""
import json
from pathlib import Path


class JSONReporter:
    """Generate JSON reports from journey analysis."""

    def generate_report(self, analysis, output_path):
        """
        Generate JSON report.

        Args:
            analysis: JourneyAnalysis object
            output_path: Path to save JSON file

        Returns:
            str: Path to generated report
        """
        report_data = analysis.to_dict()

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"✓ JSON report saved: {output_path}")
        return str(output_path)

    def generate_flow_report(self, flow_analysis, output_path):
        """
        Generate JSON report for flow analysis.

        Args:
            flow_analysis: Flow analysis dict
            output_path: Path to save JSON file

        Returns:
            str: Path to generated report
        """
        with open(output_path, 'w') as f:
            json.dump(flow_analysis, f, indent=2)

        print(f"✓ Flow analysis JSON saved: {output_path}")
        return str(output_path)
