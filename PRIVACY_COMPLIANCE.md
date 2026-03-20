# Privacy Compliance - ux-journey-scraper

**Privacy status and compliance documentation for public package**

**Package**: ux-journey-scraper
**Type**: Public (MIT License, published to PyPI)
**Status**: ✅ **COMPLIANT** (as of 2026-03-20)

---

## Privacy Status Summary

| Category | Status | Details |
|----------|--------|---------|
| **Proprietary Data** | ✅ None | No Baymard research data included |
| **Private Paths** | ✅ Clean | No hard-coded paths to proprietary data |
| **Dependencies** | ✅ Public | All dependencies are public packages |
| **Examples** | ✅ Generic | No examples using proprietary data |
| **Documentation** | ✅ Safe | No proprietary information disclosed |

**Last Audit**: 2026-03-20
**Next Review**: Before each release

---

## What This Package Contains

### ✅ Safe Content (Included)

**Code**:
- Journey capture functionality
- Browser automation (Playwright wrapper)
- Screenshot handling
- Privacy features (PII blur)
- Generic utilities

**Data**:
- Test fixtures (mock journeys)
- Example configurations (generic sites)
- Sample screenshots (test data)

**Documentation**:
- User guides
- API documentation
- Examples using public sites

### ❌ Prohibited Content (Never Include)

**Code**:
- UX analysis algorithms based on proprietary research
- Integration code requiring private dependencies
- Hard-coded proprietary data or paths

**Data**:
- Baymard Institute guidelines or test criteria
- Proprietary benchmark data
- Assessment results from proprietary analysis

**Documentation**:
- References to proprietary data locations
- Examples using proprietary guidelines
- Integration guides for private systems

---

## Compliance History

### Privacy Audit Timeline

#### March 20, 2026 - Major Privacy Cleanup ✅

**Issues Found**:
1. ❌ `UX_VALIDATION_INTEGRATION.md` - Referenced proprietary data paths
2. ❌ `examples/ux_validation_example.py` - Hard-coded path to Baymard guidelines
3. ⚠️ Multiple status docs mentioning UX validation features

**Actions Taken**:
1. ✅ Archived `UX_VALIDATION_INTEGRATION.md`
2. ✅ Archived `examples/ux_validation_example.py`
3. ✅ Archived 7 superseded status/progress documents
4. ✅ Created `archive/README.md` documenting removals
5. ✅ Updated `CONTRIBUTING.md` with privacy guidelines
6. ✅ Created this `PRIVACY_COMPLIANCE.md` file

**Result**: Package is now compliant ✅

#### Pre-March 2026 - Legacy Issues ⚠️

**v0.1.0 - v0.2.0** (Early 2026):
- ❌ Package included optional UX validation features
- ❌ Examples referenced proprietary Baymard data paths
- ❌ Documentation described integration with proprietary system

**Status**: Fixed in v0.3.0

---

## Current Architecture

### Public Package (ux-journey-scraper)

**Purpose**: Pure journey capture tool

```
ux-journey-scraper (PUBLIC)
├── Core Functionality
│   ├── Journey recording
│   ├── Autonomous crawling
│   ├── Screenshot capture
│   └── Privacy features (PII blur)
│
├── Output
│   └── journey.json + screenshots (generic data)
│
└── Dependencies
    └── Public packages only (Playwright, etc.)
```

### Private Integration (BayMAAR)

**Purpose**: UX analysis with proprietary data

```
BayMAAR (PRIVATE)
├── UX Analysis
│   ├── Guideline validation (569 Baymard guidelines)
│   ├── Scoring system (impact-weighted)
│   └── Vision-based testing
│
├── Proprietary Data
│   ├── Test criteria (1,032 criteria)
│   ├── Benchmark data (20,969 implementations)
│   └── Impact scores
│
└── Integration
    └── Reads journey.json from ux-journey-scraper
        (data coupling, not code coupling)
```

### Integration Pattern (Safe)

```
1. User: Run ux-journey-scraper
   └─> Output: journey.json (generic)

2. User: Run BayMAAR analysis (private)
   └─> Input: journey.json
   └─> Output: UX analysis (proprietary)

No code coupling between packages!
Integration via data files only.
```

---

## Optional Features & Hooks

### `ux_validation_enabled` Parameter

**Location**: `ux_journey_scraper/core/journey_recorder.py`

**Status**: ✅ **SAFE** (disabled by default)

**Why It Exists**:
- Integration hook for private BayMAAR system
- Disabled by default (`ux_validation_enabled=False`)
- No validators or data included in package
- Requires external validator to function

**Privacy Analysis**:
```python
# In journey_recorder.py:
def __init__(
    self,
    ...,
    ux_validation_enabled=False,  # ✅ Disabled by default
    guidelines_path=None,          # ✅ No default path
):
    ...
    if ux_validation_enabled:      # ✅ Only activates if explicitly enabled
        if not VALIDATORS_AVAILABLE:
            self.ux_validation_enabled = False  # ✅ Gracefully disables
```

**Verdict**:
- ✅ **COMPLIANT** - No privacy violation
- Hook exists but is inactive
- No proprietary data or code bundled
- Public users cannot use it (no validators)

---

## Compliance Checklist

### Pre-Commit Checklist

Run **BEFORE every commit**:

```bash
# 1. Check git status for proprietary files
git status
# Look for:
# - *.json files with guidelines/criteria
# - paths like .local/, baymard_backup/
# - proprietary examples

# 2. Review all changes
git diff
# Look for:
# - Hard-coded proprietary paths
# - References to Baymard data
# - Private integration code

# 3. Check for proprietary patterns
grep -r "processed_guidelines" .
grep -r ".local/baymard" .
grep -r "test-criteria" .
# Should return: No results (except in archive/)

# 4. Verify examples are generic
ls examples/
# Should contain: Only public site examples

# 5. Check documentation
grep -r "baymard_backup" *.md
grep -r "proprietary" *.md | grep -v "no proprietary"
# Should return: No problematic references
```

### Pre-Release Checklist

Run **BEFORE each PyPI release**:

- [ ] All pre-commit checks passed
- [ ] No proprietary data in package
- [ ] Examples use only public sites
- [ ] Documentation doesn't reference private systems
- [ ] Dependencies are all public packages
- [ ] README clearly states package scope (journey capture only)
- [ ] CHANGELOG doesn't mention proprietary features
- [ ] Privacy compliance status: ✅ COMPLIANT

---

## Privacy Guidelines for Contributors

### DO:

✅ Add journey capture features
✅ Improve crawling capabilities
✅ Enhance screenshot quality
✅ Add privacy features (PII blur)
✅ Improve documentation (public)
✅ Use public sites in examples

### DON'T:

❌ Add UX analysis algorithms
❌ Include Baymard guidelines data
❌ Hard-code proprietary paths
❌ Add dependencies on private packages
❌ Reference proprietary systems in docs
❌ Include assessment/scoring code

### Gray Areas (Ask First):

⚠️ Adding integration hooks (like `ux_validation_enabled`)
⚠️ Generic utilities that could be used for analysis
⚠️ Optional features that require external data

**Rule**: When in doubt, ask the maintainers.

---

## Related Documentation

### Repository Documentation (BayMAAR Mono-repo)

- [../../DATA_PRIVACY.md](../../DATA_PRIVACY.md) - Repository-wide privacy guidelines
- [../../ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture and privacy separation

### Package Documentation

- [README.md](README.md) - Package overview (states "pure journey capture")
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines (includes privacy section)
- [archive/README.md](archive/README.md) - Archived docs (privacy violations removed)

---

## Incident Response

### If Privacy Violation Is Discovered

**Immediate Actions**:
1. Do NOT commit/push the violation
2. Remove problematic files/code
3. Notify package maintainers
4. Document the issue

**For Published Violations**:
1. Yank the problematic version from PyPI immediately
2. Remove proprietary content
3. Publish fixed version
4. Update CHANGELOG explaining the issue
5. Document in this file

### Contact

**Privacy concerns**: Open issue with label `privacy`
**Maintainer contact**: See repository maintainers list

---

## Certification

**I certify that as of 2026-03-20**:
- ✅ No proprietary Baymard Institute data is included
- ✅ No hard-coded paths to proprietary data
- ✅ All examples use public sites only
- ✅ Documentation doesn't disclose proprietary information
- ✅ Package is safe for public release (MIT License)

**Audited By**: Repository documentation consolidation (Package 4)
**Date**: 2026-03-20
**Status**: ✅ **COMPLIANT**

---

**Last Updated**: 2026-03-20
**Next Audit**: Before next release

