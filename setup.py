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
    version="0.1.0",
    author="Rishabh Patel",
    author_email="rishabh@example.com",
    description="Record and analyze user journeys with automated UX guidelines validation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rishabhpatelgofynd/ux-journey-scraper",
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
    ],
    extras_require={
        "full": [
            "ecommerce-ux-guidelines>=1.2.0",  # Full UX guidelines analysis
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
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
        "Bug Reports": "https://github.com/rishabhpatelgofynd/ux-journey-scraper/issues",
        "Source": "https://github.com/rishabhpatelgofynd/ux-journey-scraper",
        "Documentation": "https://github.com/rishabhpatelgofynd/ux-journey-scraper#readme",
    },
)
