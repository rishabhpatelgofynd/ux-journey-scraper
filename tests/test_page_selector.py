"""Tests for smart page selection."""

import pytest

from ux_journey_scraper.core.page_selector import PageSelector


def test_selects_homepage():
    urls = [
        "https://example.com/",
        "https://example.com/products",
        "https://example.com/about",
    ]
    selected = PageSelector.select(urls, "example.com")
    types = {s["page_type"] for s in selected}
    assert "homepage" in types


def test_limits_pdps():
    urls = ["https://example.com/"] + [
        f"https://example.com/p/product-{i}" for i in range(100)
    ]
    selected = PageSelector.select(urls, "example.com")
    pdp_count = sum(1 for s in selected if s["page_type"] == "pdp")
    assert pdp_count <= 10


def test_limits_plps():
    urls = ["https://example.com/"] + [
        f"https://example.com/c/category-{i}" for i in range(50)
    ]
    selected = PageSelector.select(urls, "example.com")
    plp_count = sum(1 for s in selected if s["page_type"] == "plp")
    assert plp_count <= 5


def test_includes_all_policies():
    urls = [
        "https://example.com/",
        "https://example.com/privacy-policy",
        "https://example.com/terms",
        "https://example.com/refund-policy",
    ]
    selected = PageSelector.select(urls, "example.com")
    policy_count = sum(1 for s in selected if s["page_type"] == "policy")
    assert policy_count == 3


def test_includes_all_info():
    urls = [
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/contact-us",
        "https://example.com/faq",
    ]
    selected = PageSelector.select(urls, "example.com")
    info_count = sum(1 for s in selected if s["page_type"] == "info")
    assert info_count == 3


def test_limits_pagination():
    urls = ["https://example.com/"] + [
        f"https://example.com/products?page={i}" for i in range(1, 30)
    ]
    selected = PageSelector.select(urls, "example.com")
    assert len(selected) < 30


def test_returns_sorted_by_priority():
    urls = [
        "https://example.com/p/product-1",
        "https://example.com/",
        "https://example.com/privacy-policy",
        "https://example.com/cart",
    ]
    selected = PageSelector.select(urls, "example.com")
    assert selected[0]["page_type"] == "homepage"
