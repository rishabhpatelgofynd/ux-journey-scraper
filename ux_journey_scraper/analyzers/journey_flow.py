"""
Journey flow analyzer - identifies patterns and issues in user journeys.
"""


class JourneyFlowAnalyzer:
    """Analyze user journey flows for patterns and issues."""

    def analyze_flow(self, journey):
        """
        Analyze the flow of a journey.

        Args:
            journey: Journey object

        Returns:
            dict: Flow analysis results
        """
        flow_data = {
            "total_steps": len(journey.steps),
            "unique_pages": self._count_unique_pages(journey),
            "backtracking": self._detect_backtracking(journey),
            "repeated_pages": self._find_repeated_pages(journey),
            "form_interactions": self._count_form_interactions(journey),
            "navigation_patterns": self._analyze_navigation_patterns(journey),
            "journey_complexity": self._calculate_complexity(journey),
        }

        return flow_data

    def _count_unique_pages(self, journey):
        """Count unique pages visited."""
        unique_urls = set(step.url for step in journey.steps)
        return len(unique_urls)

    def _detect_backtracking(self, journey):
        """Detect if user went back to previous pages."""
        backtracking_count = 0
        visited_urls = []

        for step in journey.steps:
            if step.url in visited_urls:
                backtracking_count += 1
            visited_urls.append(step.url)

        return {
            "detected": backtracking_count > 0,
            "count": backtracking_count,
            "percentage": (backtracking_count / len(journey.steps) * 100) if journey.steps else 0,
        }

    def _find_repeated_pages(self, journey):
        """Find pages that were visited multiple times."""
        url_counts = {}

        for step in journey.steps:
            url_counts[step.url] = url_counts.get(step.url, 0) + 1

        repeated = [{"url": url, "visits": count} for url, count in url_counts.items() if count > 1]

        return sorted(repeated, key=lambda x: x["visits"], reverse=True)

    def _count_form_interactions(self, journey):
        """Count form interactions across journey."""
        total_forms = 0
        forms_with_validation = 0

        for step in journey.steps:
            forms = step.page_data.get("forms", [])
            total_forms += len(forms)

            # Check for validation (required fields)
            for form in forms:
                if any(field.get("required") for field in form.get("fields", [])):
                    forms_with_validation += 1

        return {"total_forms": total_forms, "forms_with_validation": forms_with_validation}

    def _analyze_navigation_patterns(self, journey):
        """Analyze how user navigated (links, buttons, forms)."""
        navigation_methods = {
            "link_clicks": 0,
            "form_submissions": 0,
            "button_clicks": 0,
            "direct_url": 0,
        }

        for i, step in enumerate(journey.steps):
            if i == 0:
                # First step is always direct URL
                navigation_methods["direct_url"] += 1
                continue

            # Analyze how we got to this step
            prev_step = journey.steps[i - 1]

            # Check if there's a form on previous page
            if prev_step.page_data.get("forms"):
                navigation_methods["form_submissions"] += 1
            # Check if there's a CTA button
            elif prev_step.page_data.get("ctas"):
                navigation_methods["button_clicks"] += 1
            # Otherwise assume link click
            else:
                navigation_methods["link_clicks"] += 1

        return navigation_methods

    def _calculate_complexity(self, journey):
        """Calculate journey complexity score."""
        complexity_score = 0

        # Factor 1: Number of steps
        complexity_score += min(len(journey.steps) * 2, 40)

        # Factor 2: Backtracking
        backtracking = self._detect_backtracking(journey)
        complexity_score += backtracking["count"] * 5

        # Factor 3: Unique pages ratio
        unique_ratio = (
            self._count_unique_pages(journey) / len(journey.steps) if journey.steps else 0
        )
        if unique_ratio < 0.5:  # More than half are repeated
            complexity_score += 20

        # Factor 4: Form interactions
        form_data = self._count_form_interactions(journey)
        complexity_score += form_data["total_forms"] * 10

        # Normalize to 0-100
        complexity_score = min(complexity_score, 100)

        # Categorize
        if complexity_score < 30:
            category = "simple"
        elif complexity_score < 60:
            category = "moderate"
        else:
            category = "complex"

        return {"score": complexity_score, "category": category}
