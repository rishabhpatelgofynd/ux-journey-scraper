"""
UX validators for journey scraper.

Validates pages against Baymard Institute UX guidelines.
"""

from .baymard_validator import BaymardValidator
from .guideline_index import GuidelineIndex

__all__ = ["BaymardValidator", "GuidelineIndex"]
