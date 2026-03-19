"""
Integration with the comprehensive BayMAAR UX Testing System.

This module connects the journey scraper with the existing ux_tester framework
which provides 569 guidelines, automated checks, impact scoring, and vision-based testing.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

# Add research directory to path to import ux_tester
RESEARCH_DIR = Path(__file__).parent.parent.parent.parent.parent / "research/baymaar-guidelines"
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

try:
    from ux_tester import (
        TestExecutionEngine,
        ResultAggregator,
        get_registry
    )
    from ux_scorer import UXScorer

    # Import all checks to register them
    try:
        from ux_tester.checks.homepage import check_257_logo_home, check_261_category_count
        from ux_tester.checks.navigation import *
        from ux_tester.checks.product_lists import *
        from ux_tester.checks.product_pages import *
    except ImportError as e:
        # Some checks might not be available yet
        pass

    UX_TESTER_AVAILABLE = True
except ImportError:
    UX_TESTER_AVAILABLE = False
    TestExecutionEngine = None
    ResultAggregator = None
    UXScorer = None


class ComprehensiveUXValidator:
    """
    Integrates the comprehensive BayMAAR UX Testing System with journey recording.

    This provides:
    - 569 guidelines with test criteria
    - Automated Playwright-based checks
    - Impact-weighted scoring from benchmark data
    - Vision-based testing (optional)
    - Priority recommendations
    """

    def __init__(
        self,
        test_criteria_path: Optional[str] = None,
        enable_vision_checks: bool = False,
        enable_scoring: bool = True
    ):
        """
        Initialize comprehensive UX validator.

        Args:
            test_criteria_path: Path to test-criteria-merged.json (optional)
            enable_vision_checks: Enable vision-based testing
            enable_scoring: Enable impact-weighted scoring
        """
        if not UX_TESTER_AVAILABLE:
            raise ImportError(
                "UX testing system not available. "
                "Ensure research/baymaar-guidelines is accessible."
            )

        # Initialize test execution engine
        self.execution_engine = TestExecutionEngine()

        # Initialize result aggregator
        self.aggregator = ResultAggregator()

        # Initialize scorer if enabled
        self.scorer = None
        if enable_scoring:
            if test_criteria_path:
                self.scorer = UXScorer(test_criteria_path)
            else:
                # Try default path
                default_path = RESEARCH_DIR / "test-criteria-merged.json"
                if default_path.exists():
                    self.scorer = UXScorer(str(default_path))

        self.enable_vision_checks = enable_vision_checks

        # Get registry stats
        registry = get_registry()
        self.stats = registry.get_stats()

    async def validate_page(
        self,
        page,
        url: str,
        page_type: Optional[str] = None
    ) -> Dict:
        """
        Run comprehensive UX validation on a page.

        Args:
            page: Playwright page object
            url: Page URL
            page_type: Optional page type hint (homepage, product, etc.)

        Returns:
            Comprehensive validation results with automated checks,
            impact scoring, and priority recommendations
        """
        # Run automated checks
        check_results = await self.execution_engine.run_checks_for_page(
            page, url, page_type
        )

        # Aggregate results
        aggregated = self.aggregator.aggregate(check_results)

        # Generate evidence report
        evidence_report = self.aggregator.generate_evidence_report(check_results)

        # Calculate UX score if scorer available
        ux_score = None
        grade = None
        priority_fixes = []

        if self.scorer and check_results:
            # Convert check results to scorer format
            test_results = self._convert_to_scorer_format(check_results)

            # Calculate score
            score_result = self.scorer.calculate_score(test_results)
            ux_score = score_result.get('overall_score')
            grade = score_result.get('grade')

            # Get priority recommendations
            priority_fixes = self.scorer.get_priority_recommendations(
                test_results, max_count=10
            )

        # Compile comprehensive results
        return {
            "url": url,
            "page_type": page_type or "unknown",
            "automated_checks": {
                "total_checks": len(check_results),
                "passed": sum(1 for r in check_results if r.status == "passed"),
                "failed": sum(1 for r in check_results if r.status == "failed"),
                "errors": sum(1 for r in check_results if r.status == "error"),
                "results": aggregated
            },
            "ux_score": {
                "score": ux_score,
                "grade": grade,
                "max_score": 100.0
            } if ux_score else None,
            "priority_fixes": priority_fixes,
            "evidence_report": evidence_report,
            "raw_check_results": [
                {
                    "guideline_id": r.guideline_id,
                    "check_id": r.check_id,
                    "status": r.status,
                    "evidence": r.evidence,
                    "metadata": r.metadata,
                    "error": r.error_message
                }
                for r in check_results
            ]
        }

    def _convert_to_scorer_format(self, check_results: List) -> Dict[str, str]:
        """
        Convert check results to format expected by UXScorer.

        Args:
            check_results: List of CheckResult objects

        Returns:
            Dictionary mapping guideline_id to status (passed/failed)
        """
        scorer_format = {}
        for result in check_results:
            # Map check status to scorer expected values
            if result.status == "passed":
                scorer_format[result.guideline_id] = "passed"
            elif result.status == "failed":
                scorer_format[result.guideline_id] = "failed"
            # Skip errors for scoring

        return scorer_format

    async def validate_page_batch(
        self,
        pages_data: List[Dict]
    ) -> List[Dict]:
        """
        Validate multiple pages in batch.

        Args:
            pages_data: List of dicts with 'page' and 'url' keys

        Returns:
            List of validation results
        """
        results = []

        for page_data in pages_data:
            result = await self.validate_page(
                page_data['page'],
                page_data['url'],
                page_data.get('page_type')
            )
            results.append(result)

        return results

    def get_coverage_stats(self) -> Dict:
        """
        Get statistics about test coverage.

        Returns:
            Dictionary with coverage statistics
        """
        return {
            "total_checks_registered": self.stats.get("total_checks", 0),
            "automated_checks": self.stats.get("automated_count", 0),
            "manual_checks": self.stats.get("manual_count", 0),
            "vision_checks": self.stats.get("vision_count", 0),
            "guidelines_covered": self.stats.get("unique_guidelines", 0),
            "total_guidelines": 569,  # From test-criteria-merged.json
            "coverage_percentage": round(
                (self.stats.get("unique_guidelines", 0) / 569) * 100, 1
            )
        }

    def generate_summary_report(self, validation_result: Dict) -> str:
        """
        Generate human-readable summary report.

        Args:
            validation_result: Result from validate_page()

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("UX VALIDATION SUMMARY")
        lines.append("=" * 70)
        lines.append(f"\nURL: {validation_result['url']}")
        lines.append(f"Page Type: {validation_result['page_type']}")

        # Automated checks summary
        checks = validation_result['automated_checks']
        lines.append(f"\nAutomated Checks: {checks['total_checks']} run")
        lines.append(f"  ✓ Passed: {checks['passed']}")
        lines.append(f"  ✗ Failed: {checks['failed']}")
        lines.append(f"  ⚠ Errors: {checks['errors']}")

        # UX Score
        if validation_result['ux_score']:
            score_data = validation_result['ux_score']
            lines.append(f"\nUX Score: {score_data['score']:.1f}/100 (Grade: {score_data['grade']})")

        # Priority fixes
        if validation_result['priority_fixes']:
            lines.append(f"\nTop Priority Fixes ({len(validation_result['priority_fixes'])}):")
            for i, fix in enumerate(validation_result['priority_fixes'][:5], 1):
                lines.append(f"  {i}. [{fix['guideline_id']}] {fix['title']}")
                lines.append(f"     Impact: {fix['impact']:+.1f} points")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)
