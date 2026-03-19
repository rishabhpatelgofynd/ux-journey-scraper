"""
UX validators for journey scraper.

Validates pages against Baymard Institute UX guidelines.

Two validation approaches available:
1. Simple validator (BaymardValidator) - Basic HTML-based validation
2. Comprehensive validator (ComprehensiveUXValidator) - Full testing system with
   569 guidelines, automated checks, impact scoring, and vision testing
"""

from .baymard_validator import BaymardValidator
from .guideline_index import GuidelineIndex

# Try to import comprehensive validator
try:
    from .ux_tester_integration import ComprehensiveUXValidator
    COMPREHENSIVE_VALIDATOR_AVAILABLE = True
except ImportError:
    ComprehensiveUXValidator = None
    COMPREHENSIVE_VALIDATOR_AVAILABLE = False

__all__ = [
    "BaymardValidator",
    "GuidelineIndex",
    "ComprehensiveUXValidator",
    "COMPREHENSIVE_VALIDATOR_AVAILABLE"
]
