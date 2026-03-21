"""
UX Journey Scraper - Analyze user journeys and apply UX guidelines.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="ux-journey-scraper",
    version="0.5.0",
    author="Rishabh Patel",
    author_email="rp87704@gmail.com",
    description="Autonomous web crawler for capturing user journeys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/resabh/ux-journey-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "Pillow>=10.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "urllib3>=2.0.0",
        "tqdm>=4.66.0",
        # v0.2.0 dependencies
        "pyyaml>=6.0.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "native": [
            "Appium-Python-Client>=3.1.0",
            "google-play-scraper>=1.2.0",
            "imagehash>=4.3.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ux-journey=ux_journey_scraper.cli.main:cli",
        ],
    },
    include_package_data=True,
    keywords="ux user-experience journey scraper playwright testing guidelines accessibility",
    project_urls={
        "Bug Reports": "https://github.com/resabh/ux-journey-scraper/issues",
        "Source": "https://github.com/resabh/ux-journey-scraper",
        "Documentation": "https://github.com/resabh/ux-journey-scraper#readme",
        "Changelog": "https://github.com/resabh/ux-journey-scraper/blob/main/CHANGELOG.md",
    },
)
