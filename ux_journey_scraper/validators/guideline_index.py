"""
Guideline index for fast lookup and filtering of Baymard UX guidelines.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class GuidelineIndex:
    """Efficiently index and manage Baymard UX guidelines."""

    def __init__(self, guidelines_path: str):
        """
        Initialize guideline index.

        Args:
            guidelines_path: Path to processed_guidelines.json
        """
        self.guidelines_path = Path(guidelines_path)
        self.guidelines_by_id: Dict[str, dict] = {}
        self.guidelines_by_category: Dict[str, List[dict]] = defaultdict(list)
        self.all_unique_guidelines: List[dict] = []

        self._load_and_index()

    def _load_and_index(self):
        """Load and index guidelines for fast access."""
        if not self.guidelines_path.exists():
            raise FileNotFoundError(
                f"Guidelines file not found: {self.guidelines_path}"
            )

        with open(self.guidelines_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_guidelines = data.get("guidelines", [])

        # Deduplicate by ID and create indexes
        seen_ids = set()
        for guideline in all_guidelines:
            gid = guideline["id"]

            # Only add unique guidelines
            if gid not in seen_ids:
                seen_ids.add(gid)

                # Index by ID
                self.guidelines_by_id[gid] = guideline

                # Index by category
                category = guideline["category"]
                self.guidelines_by_category[category].append(guideline)

                # Add to all unique
                self.all_unique_guidelines.append(guideline)

    def get_by_id(self, guideline_id: str) -> Optional[dict]:
        """
        Get a guideline by ID.

        Args:
            guideline_id: Guideline ID (e.g., "237")

        Returns:
            Guideline dict or None if not found
        """
        return self.guidelines_by_id.get(guideline_id)

    def get_by_category(self, category: str) -> List[dict]:
        """
        Get all guidelines for a category.

        Args:
            category: Category name (e.g., "Homepage", "Search & Discovery")

        Returns:
            List of guidelines
        """
        return self.guidelines_by_category.get(category, [])

    def get_all_categories(self) -> List[str]:
        """Get list of all categories."""
        return list(self.guidelines_by_category.keys())

    def get_all_unique(self) -> List[dict]:
        """Get all unique guidelines."""
        return self.all_unique_guidelines

    def get_total_count(self) -> int:
        """Get total number of unique guidelines."""
        return len(self.all_unique_guidelines)

    def search_by_keyword(self, keyword: str) -> List[dict]:
        """
        Search guidelines by keyword in title or insights.

        Args:
            keyword: Search term

        Returns:
            List of matching guidelines
        """
        keyword_lower = keyword.lower()
        results = []

        for guideline in self.all_unique_guidelines:
            # Search in title
            if keyword_lower in guideline["title"].lower():
                results.append(guideline)
                continue

            # Search in insights
            for insight in guideline.get("insights", []):
                if keyword_lower in insight.lower():
                    results.append(guideline)
                    break

        return results

    def get_high_severity_guidelines(self) -> List[dict]:
        """
        Get guidelines marked as high severity (Essential).

        Returns:
            List of high severity guidelines
        """
        high_severity = []

        for guideline in self.all_unique_guidelines:
            content = guideline.get("content_preview", "").lower()
            if "essential" in content:
                high_severity.append(guideline)

        return high_severity

    def get_guidelines_for_page_type(self, page_type: str) -> List[dict]:
        """
        Get guidelines for a specific page type.

        Args:
            page_type: Page type (homepage, product, cart, checkout, etc.)

        Returns:
            List of relevant guidelines
        """
        # Map common page types to categories
        page_type_mapping = {
            "homepage": ["Homepage"],
            "home": ["Homepage"],
            "landing": ["Homepage"],
            "search": ["Search & Discovery"],
            "search_results": ["Search & Discovery"],
            "product": ["Product Page"],
            "product_page": ["Product Page"],
            "pdp": ["Product Page"],
            "category": ["Navigation & Taxonomy", "Product Lists"],
            "listing": ["Product Lists"],
            "cart": ["Cart"],
            "shopping_cart": ["Cart"],
            "checkout": ["Checkout"],
            "payment": ["Checkout"],
            "navigation": ["Navigation & Taxonomy"],
        }

        page_type_lower = page_type.lower()
        categories = page_type_mapping.get(page_type_lower, [])

        # Collect all guidelines from mapped categories
        guidelines = []
        for category in categories:
            guidelines.extend(self.get_by_category(category))

        # If no mapping found, try partial match
        if not guidelines:
            for category in self.get_all_categories():
                if page_type_lower in category.lower():
                    guidelines.extend(self.get_by_category(category))

        return guidelines

    def get_statistics(self) -> Dict:
        """
        Get statistics about the guideline index.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_unique_guidelines": len(self.all_unique_guidelines),
            "total_categories": len(self.guidelines_by_category),
            "categories": {
                category: len(guidelines)
                for category, guidelines in self.guidelines_by_category.items()
            },
            "high_severity_count": len(self.get_high_severity_guidelines()),
        }

    def export_for_validation(self, output_path: str):
        """
        Export guideline index in a format optimized for validation.

        Args:
            output_path: Path to save the exported index
        """
        validation_index = {
            "metadata": {
                "total_guidelines": len(self.all_unique_guidelines),
                "categories": list(self.guidelines_by_category.keys()),
                "source": str(self.guidelines_path),
            },
            "guidelines": self.all_unique_guidelines,
            "by_category": {
                category: [g["id"] for g in guidelines]
                for category, guidelines in self.guidelines_by_category.items()
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(validation_index, f, indent=2)

        print(f"✓ Exported validation index to {output_path}")
