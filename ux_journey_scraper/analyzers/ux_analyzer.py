"""
UX analyzer - integrates with ecommerce-ux-guidelines package.
"""
from datetime import datetime

try:
    from ecommerce_ux_guidelines import AccessibilityValidator, GuidelineEngine, Validator

    HAS_GUIDELINES = True
except ImportError:
    HAS_GUIDELINES = False
    print("Warning: ecommerce-ux-guidelines not installed. UX analysis will be limited.")


class StepAnalysis:
    """Analysis results for a single journey step."""

    def __init__(self, step_number, url, title):
        self.step_number = step_number
        self.url = url
        self.title = title
        self.ux_violations = []
        self.accessibility_issues = []
        self.overall_score = 100.0
        self.page_type = "general"

    def add_violation(self, violation):
        """Add a UX violation."""
        self.ux_violations.append(violation)

        # Deduct from score based on severity
        severity_penalties = {"critical": 15, "major": 8, "minor": 3}
        penalty = severity_penalties.get(violation.get("severity", "minor"), 3)
        self.overall_score = max(0, self.overall_score - penalty)

    def add_accessibility_issue(self, issue):
        """Add an accessibility issue."""
        self.accessibility_issues.append(issue)

        # Deduct from score
        severity_penalties = {"critical": 12, "major": 6, "minor": 2}
        penalty = severity_penalties.get(issue.get("severity", "minor"), 2)
        self.overall_score = max(0, self.overall_score - penalty)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "url": self.url,
            "title": self.title,
            "page_type": self.page_type,
            "overall_score": round(self.overall_score, 1),
            "ux_violations": self.ux_violations,
            "accessibility_issues": self.accessibility_issues,
            "total_issues": len(self.ux_violations) + len(self.accessibility_issues),
        }


class JourneyAnalysis:
    """Complete analysis of a user journey."""

    def __init__(self, journey):
        self.journey = journey
        self.step_analyses = []
        self.overall_score = 0.0
        self.total_violations = 0
        self.total_accessibility_issues = 0
        self.analysis_timestamp = datetime.now().isoformat()

    def add_step_analysis(self, analysis):
        """Add analysis for a step."""
        self.step_analyses.append(analysis)

    def calculate_overall_score(self):
        """Calculate overall journey score."""
        if not self.step_analyses:
            return 0.0

        total_score = sum(step.overall_score for step in self.step_analyses)
        self.overall_score = total_score / len(self.step_analyses)

        # Count total issues
        self.total_violations = sum(len(step.ux_violations) for step in self.step_analyses)
        self.total_accessibility_issues = sum(
            len(step.accessibility_issues) for step in self.step_analyses
        )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "journey_info": {
                "start_url": self.journey.start_url,
                "total_steps": len(self.journey.steps),
                "start_time": self.journey.start_time,
                "end_time": self.journey.end_time,
            },
            "analysis_timestamp": self.analysis_timestamp,
            "overall_score": round(self.overall_score, 1),
            "total_violations": self.total_violations,
            "total_accessibility_issues": self.total_accessibility_issues,
            "step_analyses": [step.to_dict() for step in self.step_analyses],
        }


class UXAnalyzer:
    """Analyze journeys using ecommerce-ux-guidelines."""

    def __init__(self, guideline_priority="all"):
        """
        Initialize UX analyzer.

        Args:
            guideline_priority: Priority level ('essential', 'high', 'all')
        """
        self.guideline_priority = guideline_priority

        if HAS_GUIDELINES:
            self.engine = GuidelineEngine()
            self.validator = Validator(self.engine)
            self.a11y_validator = AccessibilityValidator(self.engine)
        else:
            self.engine = None
            self.validator = None
            self.a11y_validator = None

    def analyze(self, journey):
        """
        Analyze a complete journey.

        Args:
            journey: Journey object to analyze

        Returns:
            JourneyAnalysis: Analysis results
        """
        print(f"\n🔍 Analyzing journey...")
        print(f"📊 Total steps: {len(journey.steps)}")

        analysis = JourneyAnalysis(journey)

        for step in journey.steps:
            print(f"\n   Analyzing Step {step.step_number}: {step.title}...")
            step_analysis = self._analyze_step(step)
            analysis.add_step_analysis(step_analysis)

            print(f"      Score: {step_analysis.overall_score}/100")
            print(
                f"      Issues: {len(step_analysis.ux_violations)} UX, "
                f"{len(step_analysis.accessibility_issues)} A11y"
            )

        # Calculate overall score
        analysis.calculate_overall_score()

        print(f"\n✅ Analysis complete!")
        print(f"📈 Overall Score: {analysis.overall_score}/100")
        print(
            f"⚠️  Total Issues: {analysis.total_violations + analysis.total_accessibility_issues}"
        )

        return analysis

    def _analyze_step(self, step):
        """Analyze a single journey step."""
        step_analysis = StepAnalysis(step.step_number, step.url, step.title)

        # Determine page type from URL
        step_analysis.page_type = self._detect_page_type(step.url)

        if not HAS_GUIDELINES:
            # Limited analysis without guidelines package
            step_analysis.add_violation(
                {
                    "severity": "minor",
                    "issue": "ecommerce-ux-guidelines not installed - limited analysis",
                    "fix": "Install ecommerce-ux-guidelines for full UX validation",
                }
            )
            return step_analysis

        try:
            # Validate with ecommerce-ux-guidelines
            html = step.page_data.get("html", "")

            # Run UX validation
            ux_result = self.validator.validate_html(html, page_type=step_analysis.page_type)

            # Extract violations
            for violation in ux_result.violations:
                step_analysis.add_violation(
                    {
                        "guideline_id": getattr(violation, "guideline_id", ""),
                        "severity": getattr(violation, "severity", "minor"),
                        "issue": getattr(violation, "issue", ""),
                        "fix": getattr(violation, "fix", ""),
                        "element": getattr(violation, "element", ""),
                    }
                )

            # Run accessibility validation
            a11y_result = self.a11y_validator.validate_html(html, page_type=step_analysis.page_type)

            # Extract accessibility issues
            for issue in a11y_result.violations:
                step_analysis.add_accessibility_issue(
                    {
                        "wcag_criterion": getattr(issue, "wcag_criterion", ""),
                        "severity": getattr(issue, "severity", "minor"),
                        "issue": getattr(issue, "issue", ""),
                        "fix": getattr(issue, "fix", ""),
                        "element": getattr(issue, "element", ""),
                    }
                )

        except Exception as e:
            print(f"      Warning: Analysis error: {e}")
            step_analysis.add_violation(
                {
                    "severity": "minor",
                    "issue": f"Analysis error: {str(e)}",
                    "fix": "Check HTML structure and try again",
                }
            )

        return step_analysis

    def _detect_page_type(self, url):
        """
        Detect page type from URL.

        Args:
            url: Page URL

        Returns:
            str: Page type (landing, product, checkout, etc.)
        """
        url_lower = url.lower()

        if any(keyword in url_lower for keyword in ["checkout", "cart", "basket"]):
            return "checkout"
        elif any(keyword in url_lower for keyword in ["product", "item", "/p/", "/pd/"]):
            return "product"
        elif any(keyword in url_lower for keyword in ["search", "results"]):
            return "search"
        elif any(keyword in url_lower for keyword in ["category", "collection", "listing"]):
            return "listing"
        else:
            return "landing"
