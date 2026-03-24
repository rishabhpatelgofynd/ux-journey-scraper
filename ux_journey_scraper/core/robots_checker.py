"""
robots.txt checker with user confirmation.
"""

import urllib.robotparser
from urllib.parse import urlparse


class RobotsChecker:
    """Check robots.txt and ask for user confirmation if needed."""

    def __init__(self, user_agent="UX-Journey-Scraper/0.1.0"):
        self.user_agent = user_agent
        self._parsers = {}  # Cache parsers by domain

    def can_fetch(self, url):
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            bool: True if allowed, False if disallowed
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Get or create parser for this domain
        if domain not in self._parsers:
            parser = urllib.robotparser.RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            try:
                parser.set_url(robots_url)
                parser.read()
                self._parsers[domain] = parser
            except Exception:
                # If robots.txt doesn't exist or can't be read, allow by default
                return True

        parser = self._parsers[domain]
        return parser.can_fetch(self.user_agent, url)

    def check_with_confirmation(self, url, interactive=True):
        """
        Check robots.txt and ask user for confirmation if disallowed.

        Args:
            url: URL to check
            interactive: If True, ask user for confirmation. If False, respect robots.txt strictly.

        Returns:
            bool: True if should proceed, False if should skip

        Raises:
            ValueError: If robots.txt disallows and user declines
        """
        can_fetch = self.can_fetch(url)

        if can_fetch:
            return True

        # URL is disallowed by robots.txt
        if not interactive:
            print(f"⚠️  robots.txt disallows crawling: {url}")
            return False

        # Ask user for confirmation
        print(f"\n⚠️  robots.txt Restriction Detected")
        print(f"URL: {url}")
        print(f"The robots.txt file for this site disallows automated access.")
        print(f"\nOptions:")
        print(f"  [y] Proceed anyway (override robots.txt)")
        print(f"  [n] Skip this URL (respect robots.txt)")

        while True:
            response = input("\nYour choice (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                print("✓ Proceeding with scraping (robots.txt overridden)")
                return True
            elif response in ["n", "no"]:
                print("✓ Skipping URL (respecting robots.txt)")
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
