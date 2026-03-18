#!/bin/bash
#
# Pre-publish checklist for UX Journey Scraper
# Run this before creating a GitHub release
#

set -e

echo "🔍 Pre-Publish Checklist for UX Journey Scraper"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Function to check a condition
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to warn
warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Version Consistency"
echo "----------------------"

# Extract versions
VERSION_PYPROJECT=$(grep "^version = " pyproject.toml | cut -d'"' -f2)
VERSION_SETUP=$(grep "version=" setup.py | head -1 | cut -d'"' -f2)

echo "   pyproject.toml: $VERSION_PYPROJECT"
echo "   setup.py: $VERSION_SETUP"

if [ "$VERSION_PYPROJECT" = "$VERSION_SETUP" ]; then
    check "Versions match"
else
    echo -e "${RED}✗${NC} Versions don't match!"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "2. Code Quality"
echo "---------------"

# Check if black is installed
if command -v black &> /dev/null; then
    black --check ux_journey_scraper/ tests/ > /dev/null 2>&1
    check "Code formatted with black"
else
    warn "Black not installed (run: pip install black)"
fi

# Check if isort is installed
if command -v isort &> /dev/null; then
    isort --check-only ux_journey_scraper/ tests/ > /dev/null 2>&1
    check "Imports sorted with isort"
else
    warn "isort not installed (run: pip install isort)"
fi

# Check if flake8 is installed
if command -v flake8 &> /dev/null; then
    flake8 ux_journey_scraper/ tests/ --select=E9,F63,F7,F82 > /dev/null 2>&1
    check "No critical linting errors"
else
    warn "flake8 not installed (run: pip install flake8)"
fi

echo ""
echo "3. Tests"
echo "--------"

# Run tests
if command -v pytest &> /dev/null; then
    pytest tests/ -v -m "not integration" > /dev/null 2>&1
    check "All unit tests pass"
else
    warn "pytest not installed (run: pip install pytest)"
fi

echo ""
echo "4. Documentation"
echo "----------------"

# Check README exists
if [ -f "README.md" ]; then
    check "README.md exists"
else
    echo -e "${RED}✗${NC} README.md missing!"
    ERRORS=$((ERRORS + 1))
fi

# Check CHANGELOG exists
if [ -f "CHANGELOG.md" ]; then
    check "CHANGELOG.md exists"
else
    warn "CHANGELOG.md missing (recommended)"
fi

# Check LICENSE exists
if [ -f "LICENSE" ]; then
    check "LICENSE exists"
else
    warn "LICENSE missing (recommended)"
fi

echo ""
echo "5. Package Build"
echo "----------------"

# Try building package
if command -v python &> /dev/null; then
    python -m build > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        check "Package builds successfully"

        # Check with twine
        if command -v twine &> /dev/null; then
            twine check dist/* > /dev/null 2>&1
            check "Package passes twine check"
        else
            warn "twine not installed (run: pip install twine)"
        fi
    else
        echo -e "${RED}✗${NC} Package build failed!"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗${NC} Python not found!"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "6. Git Status"
echo "-------------"

# Check if git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        check "No uncommitted changes"
    else
        warn "Uncommitted changes detected - commit before release"
    fi

    # Check if on main branch
    BRANCH=$(git branch --show-current)
    if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
        check "On main branch"
    else
        warn "Not on main branch (current: $BRANCH)"
    fi

    # Check if pushed
    if git diff origin/$(git branch --show-current)..HEAD --quiet 2>/dev/null; then
        check "All changes pushed to remote"
    else
        warn "Local commits not pushed to remote"
    fi
else
    warn "Not a git repository"
fi

echo ""
echo "7. Required Files"
echo "-----------------"

REQUIRED_FILES=(
    "ux_journey_scraper/__init__.py"
    "setup.py"
    "pyproject.toml"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check "$file exists"
    else
        echo -e "${RED}✗${NC} $file missing!"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "================================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to publish.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Update version in pyproject.toml and setup.py"
    echo "  2. Update CHANGELOG.md with release notes"
    echo "  3. Commit changes: git commit -am \"Bump version to $VERSION_PYPROJECT\""
    echo "  4. Create tag: git tag -a v$VERSION_PYPROJECT -m \"Release v$VERSION_PYPROJECT\""
    echo "  5. Push: git push && git push --tags"
    echo "  6. Create GitHub release to trigger PyPI publication"
    echo ""
    echo "See PUBLISHING.md for detailed instructions."
    exit 0
else
    echo -e "${RED}❌ $ERRORS check(s) failed. Fix issues before publishing.${NC}"
    exit 1
fi
