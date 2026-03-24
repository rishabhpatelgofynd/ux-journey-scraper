# Publishing to PyPI - Step-by-Step Guide

This guide walks through publishing the UX Journey Scraper package to PyPI.

## Prerequisites

Before publishing, ensure:

- ✅ All tests pass (`pytest tests/`)
- ✅ Code is formatted (`black . && isort .`)
- ✅ Linting passes (`flake8 .`)
- ✅ Documentation is up to date
- ✅ CHANGELOG.md is updated with release notes
- ✅ Version number is bumped in `pyproject.toml` and `setup.py`

## Step 1: Create PyPI Account

### 1.1 Register on PyPI

1. Go to <https://pypi.org/account/register/>
2. Fill in:
   - Username: `resabh` (or your preferred username)
   - Email: `rp87704@gmail.com`
   - Password: (use a strong password)
3. Verify your email address

### 1.2 Enable Two-Factor Authentication (Recommended)

1. Go to <https://pypi.org/manage/account/>
2. Click "Add 2FA" under "Two Factor Authentication"
3. Choose TOTP app (Google Authenticator, Authy, etc.)
4. Scan QR code and enter verification code
5. Save recovery codes securely

### 1.3 Generate Recovery Codes

PyPI will provide recovery codes. **Save these securely!** You'll need them if you lose access to your 2FA device.

## Step 2: Configure Trusted Publishing (Recommended)

Trusted publishing allows GitHub Actions to publish to PyPI without API tokens.

### 2.1 Add Trusted Publisher on PyPI

1. Go to <https://pypi.org/manage/account/publishing/>
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name:** `ux-journey-scraper`
   - **Owner:** `resabh` (your GitHub username)
   - **Repository name:** `ux-journey-scraper` (or your repo name)
   - **Workflow name:** `ci.yml`
   - **Environment name:** (leave empty)
4. Click "Add"

This creates a "pending publisher" that will be activated when you first publish.

### 2.2 Verify GitHub Actions Workflow

The CI/CD pipeline (`. github/workflows/ci.yml`) is already configured for trusted publishing:

```yaml
publish:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs: [lint, test, build]
  if: github.event_name == 'release' && github.event.action == 'published'
  permissions:
    id-token: write  # Required for trusted publishing
  steps:
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        skip-existing: true
```

## Step 3: Prepare Release

### 3.1 Update Version Number

Update version in **both** files:

**pyproject.toml:**

```toml
[project]
name = "ux-journey-scraper"
version = "0.1.0"  # Change to new version
```

**setup.py:**

```python
setup(
    name="ux-journey-scraper",
    version="0.1.0",  # Change to new version (must match pyproject.toml)
    ...
)
```

Version format: `MAJOR.MINOR.PATCH` (e.g., `0.1.0`, `0.2.0`, `1.0.0`)

### 3.2 Update CHANGELOG.md

Create or update `CHANGELOG.md`:

```markdown
# Changelog

## [0.1.0] - 2026-03-19

### Added
- Initial release
- Journey recording with Playwright
- PII blurring in screenshots
- UX guideline analysis (324+ guidelines)
- WCAG 2.1 accessibility validation
- Robots.txt compliance
- Interactive HTML reports
- CLI tool

### Fixed
- None (initial release)

### Changed
- None (initial release)

## [Unreleased]
```

### 3.3 Commit Changes

```bash
git add pyproject.toml setup.py CHANGELOG.md
git commit -m "Bump version to 0.1.0"
git push origin main
```

## Step 4: Create GitHub Release

### 4.1 Create Git Tag

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release v0.1.0"

# Push tag to GitHub
git push origin v0.1.0
```

### 4.2 Create GitHub Release

#### Option A: Using GitHub CLI

```bash
# Install GitHub CLI if needed
brew install gh  # macOS
# or: sudo apt install gh  # Linux

# Authenticate
gh auth login

# Create release
gh release create v0.1.0 \
  --title "UX Journey Scraper v0.1.0" \
  --notes "First stable release.

**Features:**
- Journey recording with Playwright
- PII blurring in screenshots
- UX guideline analysis (324+ guidelines)
- WCAG 2.1 accessibility validation
- Interactive HTML reports

**Installation:**
\`\`\`bash
pip install ux-journey-scraper
\`\`\`

See [CHANGELOG.md](CHANGELOG.md) for full details."
```

#### Option B: Using GitHub Web Interface

1. Go to <https://github.com/resabh/ux-journey-scraper/releases/new>
2. Fill in:
   - **Tag version:** `v0.1.0` (select existing tag)
   - **Release title:** `UX Journey Scraper v0.1.0`
   - **Description:** Copy release notes from CHANGELOG.md
3. Check "Set as the latest release"
4. Click "Publish release"

### 4.3 Monitor CI/CD Pipeline

1. Go to <https://github.com/resabh/ux-journey-scraper/actions>
2. Watch the "CI/CD Pipeline" workflow
3. Verify all jobs pass:
   - ✅ Lint Code
   - ✅ Test Python 3.9, 3.10, 3.11, 3.12
   - ✅ Code Coverage
   - ✅ Build Package
   - ✅ Publish to PyPI

The publish job will automatically upload to PyPI.

## Step 5: Verify Publication

### 5.1 Check PyPI Package Page

1. Go to <https://pypi.org/project/ux-journey-scraper/>
2. Verify:
   - Package name and version are correct
   - README.md is displayed
   - Installation instructions are clear
   - Project links work (GitHub, documentation, issues)
   - Classifiers are correct

### 5.2 Test Installation

In a new virtual environment:

```bash
# Create fresh virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from PyPI
pip install ux-journey-scraper

# Verify installation
ux-journey --version

# Install Playwright browsers
playwright install chromium

# Test basic functionality
ux-journey --help
```

### 5.3 Test Package Functionality

Create a test script:

```python
# test_package.py
from ux_journey_scraper.cli.main import cli

print("✅ Package imported successfully!")
```

Run it:

```bash
python test_package.py
```

## Step 6: Post-Publication

### 6.1 Update README Badges

Update installation instructions in README.md:

```markdown
## Installation

```bash
pip install ux-journey-scraper
```

Add PyPI badges:

```markdown
[![PyPI version](https://badge.fury.io/py/ux-journey-scraper.svg)](https://pypi.org/project/ux-journey-scraper/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ux-journey-scraper)](https://pypi.org/project/ux-journey-scraper/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/ux-journey-scraper)](https://pypi.org/project/ux-journey-scraper/)
```

### 6.2 Announce Release

Consider announcing the release on:

- GitHub Discussions
- Twitter/X
- Reddit (r/Python, r/webdev, r/userexperience)
- Dev.to or Medium (write a blog post)
- Hacker News

### 6.3 Monitor Issues

Watch for:

- Installation issues
- Bug reports
- Feature requests
- Questions from users

## Alternative: Manual Publishing (Not Recommended)

If you prefer not to use trusted publishing:

### Create API Token

1. Go to <https://pypi.org/manage/account/token/>
2. Click "Add API token"
3. Token name: `ux-journey-scraper-publish`
4. Scope: "Project: ux-journey-scraper"
5. Copy token (starts with `pypi-`)

### Add Token to GitHub Secrets

1. Go to repository Settings → Secrets → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: (paste token)

### Update Workflow

Modify `.github/workflows/ci.yml`:

```yaml
- name: Publish to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: twine upload dist/*
```

## Troubleshooting

### "File already exists" Error

If you try to upload the same version twice:

- Bump the version number
- Delete and recreate the tag
- Create a new release

### "Invalid or non-existent authentication" Error

- Verify trusted publisher configuration matches exactly
- Check PyPI project name matches `pyproject.toml`
- Ensure workflow name is `ci.yml`
- Verify repository owner and name are correct

### Tests Fail in CI

- Run tests locally: `pytest tests/`
- Check Python version compatibility
- Verify all dependencies are in `setup.py` or `pyproject.toml`

### Package Not Found After Publishing

- Wait 1-2 minutes for PyPI to index
- Check package name spelling
- Verify publication succeeded in GitHub Actions

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | TBD | Initial release |

## Next Steps After v0.1.0

1. **Monitor Downloads:** Track PyPI stats
2. **Gather Feedback:** Listen to user issues and feature requests
3. **Plan v0.2.0:** Identify features for next release
4. **Documentation:** Write comprehensive docs (ReadTheDocs)
5. **Examples:** Create example projects using the tool
6. **CI/CD:** Add automated release notes generation

## Resources

- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
