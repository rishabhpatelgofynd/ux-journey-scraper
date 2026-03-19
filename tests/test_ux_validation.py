"""
Tests for UX validation integration.
"""
import pytest
from pathlib import Path

# Test if validators can be imported
def test_validator_imports():
    """Test that validator modules can be imported."""
    try:
        from ux_journey_scraper.validators import BaymardValidator, GuidelineIndex
        assert BaymardValidator is not None
        assert GuidelineIndex is not None
        print("✅ Validator imports successful")
    except ImportError as e:
        pytest.fail(f"Failed to import validators: {e}")


def test_guideline_index():
    """Test GuidelineIndex functionality."""
    from ux_journey_scraper.validators import GuidelineIndex

    # Path to guidelines
    guidelines_path = Path(__file__).parent.parent.parent.parent / ".local/baymard-scraper/data/raw/baymard_backup/processed_guidelines.json"

    if not guidelines_path.exists():
        pytest.skip(f"Guidelines file not found at {guidelines_path}")

    # Initialize index
    index = GuidelineIndex(str(guidelines_path))

    # Test basic functionality
    assert index.get_total_count() > 0, "Should have guidelines"
    print(f"✅ Loaded {index.get_total_count()} guidelines")

    # Test category lookup
    categories = index.get_all_categories()
    assert len(categories) > 0, "Should have categories"
    print(f"✅ Found {len(categories)} categories: {categories}")

    # Test ID lookup
    guideline = index.get_by_id("237")
    assert guideline is not None, "Should find guideline #237"
    assert guideline["title"] == "Feature a Broad Range of Product Types on the Homepage"
    print(f"✅ Guideline #237: {guideline['title']}")

    # Test page type mapping
    homepage_guidelines = index.get_guidelines_for_page_type("homepage")
    assert len(homepage_guidelines) > 0, "Should have homepage guidelines"
    print(f"✅ Found {len(homepage_guidelines)} homepage guidelines")

    # Test statistics
    stats = index.get_statistics()
    assert "total_unique_guidelines" in stats
    print(f"✅ Statistics: {stats['total_unique_guidelines']} total guidelines")


def test_baymard_validator():
    """Test BaymardValidator functionality."""
    from ux_journey_scraper.validators import BaymardValidator, GuidelineIndex

    guidelines_path = Path(__file__).parent.parent.parent.parent / ".local/baymard-scraper/data/raw/baymard_backup/processed_guidelines.json"

    if not guidelines_path.exists():
        pytest.skip(f"Guidelines file not found at {guidelines_path}")

    # Initialize
    index = GuidelineIndex(str(guidelines_path))
    validator = BaymardValidator(index)

    # Test page type detection
    page_type = validator.detect_page_type(
        url="https://example.com",
        html="<html><body><h1>Welcome</h1></body></html>",
        title="Homepage"
    )
    assert page_type == "homepage"
    print(f"✅ Page type detection: {page_type}")

    # Test validation
    sample_html = """
    <html>
    <head><title>Test Homepage</title></head>
    <body>
        <nav>
            <a href="/products">Products</a>
            <a href="/about">About</a>
        </nav>
        <h1>Welcome to Our Store</h1>
        <div class="product-grid">
            <div class="product">Product 1</div>
            <div class="product">Product 2</div>
        </div>
    </body>
    </html>
    """

    validation = validator.validate_page(
        url="https://example.com",
        html=sample_html,
        title="Test Homepage"
    )

    # Check validation structure
    assert "page_url" in validation
    assert "page_type" in validation
    assert "compliance_score" in validation
    assert "violations" in validation
    assert "warnings" in validation
    assert "passed" in validation

    print(f"✅ Validation result:")
    print(f"   Page Type: {validation['page_type']}")
    print(f"   Compliance Score: {validation['compliance_score']}%")
    print(f"   Guidelines Checked: {validation['total_guidelines_checked']}")
    print(f"   Violations: {len(validation['violations'])}")
    print(f"   Warnings: {len(validation['warnings'])}")
    print(f"   Passed: {len(validation['passed'])}")

    # Test validation coverage
    coverage = validator.get_validation_coverage()
    assert "total_guidelines" in coverage
    assert "implemented_validations" in coverage
    assert "coverage_percentage" in coverage
    print(f"✅ Validation coverage: {coverage['coverage_percentage']}%")


def test_config_integration():
    """Test configuration integration."""
    from ux_journey_scraper.config.scrape_config import UXValidationConfig

    # Test default config
    config = UXValidationConfig()
    assert config.enabled == False
    assert config.auto_detect_page_type == True
    print("✅ Default UX validation config created")

    # Test enabled config
    guidelines_path = Path(__file__).parent.parent.parent.parent / ".local/baymard-scraper/data/raw/baymard_backup/processed_guidelines.json"

    if guidelines_path.exists():
        config = UXValidationConfig(
            enabled=True,
            guidelines_path=str(guidelines_path),
            min_compliance_score=70.0,
            severity_threshold="high"
        )
        assert config.enabled == True
        assert config.min_compliance_score == 70.0
        assert config.severity_threshold == "high"
        print("✅ Custom UX validation config created")


if __name__ == "__main__":
    """Run tests manually."""
    print("\n" + "="*60)
    print("UX VALIDATION INTEGRATION TESTS")
    print("="*60 + "\n")

    try:
        print("Test 1: Validator Imports")
        test_validator_imports()
        print()

        print("Test 2: Guideline Index")
        test_guideline_index()
        print()

        print("Test 3: Baymard Validator")
        test_baymard_validator()
        print()

        print("Test 4: Config Integration")
        test_config_integration()
        print()

        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
