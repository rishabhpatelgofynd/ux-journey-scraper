"""Tests for design data collector."""
import pytest


def test_design_data_collector_imports():
    from ux_journey_scraper.core.design_data_collector import DesignDataCollector
    collector = DesignDataCollector()
    assert collector is not None


def test_css_variables_js():
    from ux_journey_scraper.core.design_data_collector import DesignDataCollector
    collector = DesignDataCollector()
    assert isinstance(collector.CSS_VARS_JS, str)
    assert "getComputedStyle" in collector.CSS_VARS_JS


def test_component_tree_js():
    from ux_journey_scraper.core.design_data_collector import DesignDataCollector
    collector = DesignDataCollector()
    assert isinstance(collector.COMPONENT_TREE_JS, str)


def test_asset_urls_js():
    from ux_journey_scraper.core.design_data_collector import DesignDataCollector
    collector = DesignDataCollector()
    assert isinstance(collector.ASSET_URLS_JS, str)


def test_all_styles_js():
    from ux_journey_scraper.core.design_data_collector import DesignDataCollector
    collector = DesignDataCollector()
    assert isinstance(collector.ALL_STYLES_JS, str)
    assert "getComputedStyle" in collector.ALL_STYLES_JS
