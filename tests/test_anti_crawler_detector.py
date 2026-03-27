"""Tests for anti-crawler detection."""
import pytest
from ux_journey_scraper.core.anti_crawler_detector import AntiCrawlerDetector


class TestHoneypotDetection:
    def test_visible_link_not_honeypot(self):
        assert not AntiCrawlerDetector.is_honeypot_link({"display": "block", "visibility": "visible", "opacity": "1"})

    def test_display_none_is_honeypot(self):
        assert AntiCrawlerDetector.is_honeypot_link({"display": "none", "visibility": "visible", "opacity": "1"})

    def test_hidden_visibility_is_honeypot(self):
        assert AntiCrawlerDetector.is_honeypot_link({"display": "block", "visibility": "hidden", "opacity": "1"})

    def test_zero_opacity_is_honeypot(self):
        assert AntiCrawlerDetector.is_honeypot_link({"display": "block", "visibility": "visible", "opacity": "0"})


class TestPaginationDetection:
    def test_detects_pagination(self):
        assert AntiCrawlerDetector.is_pagination_url("https://example.com/products?page=5")
        assert AntiCrawlerDetector.is_pagination_url("https://example.com/page/3")
        assert AntiCrawlerDetector.is_pagination_url("https://example.com/products?offset=40")

    def test_not_pagination(self):
        assert not AntiCrawlerDetector.is_pagination_url("https://example.com/products/shoes")

    def test_pagination_limit(self):
        urls = [f"https://example.com/products?page={i}" for i in range(1, 20)]
        limited = AntiCrawlerDetector.limit_pagination(urls, max_per_pattern=5)
        assert len(limited) == 5


class TestEmptyPageDetection:
    def test_empty_page(self):
        assert AntiCrawlerDetector.is_empty_page("<html><body><div id='root'></div></body></html>", "")

    def test_real_page(self):
        html = "<html><body><h1>Welcome</h1><p>" + "Content " * 50 + "</p></body></html>"
        assert not AntiCrawlerDetector.is_empty_page(html, "Welcome " + "Content " * 50)


class TestBlockDetection:
    def test_access_denied(self):
        assert AntiCrawlerDetector.is_block_page("Access Denied", "You don't have permission")

    def test_captcha(self):
        assert AntiCrawlerDetector.is_block_page("Verify", "Please verify you are human")

    def test_cloudflare(self):
        assert AntiCrawlerDetector.is_block_page("Just a moment...", "Checking your browser")

    def test_normal_page(self):
        assert not AntiCrawlerDetector.is_block_page("Buy Shoes Online", "Great selection of shoes")
