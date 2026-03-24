# ux-journey-scraper - Archived Documentation

**Documentation superseded or moved for privacy/organization reasons**

**Archive Date**: 2026-03-20
**Reason**: Privacy compliance + documentation consolidation

---

## Privacy Compliance Archive

### Files Removed for Privacy

**1. UX_VALIDATION_INTEGRATION.md** ⚠️ PRIVACY ISSUE

- **Why Archived**: Referenced proprietary Baymard Institute data paths
- **Issue**: Contained examples with `.local/baymard-scraper/data/raw/baymard_backup/processed_guidelines.json`
- **Status**: Feature removed from public package, moved to BayMAAR (private)
- **See**: BayMAAR repository for UX analysis features

**2. examples/ux_validation_example.py** ⚠️ PRIVACY ISSUE

- **Why Archived**: Example code referencing proprietary data paths
- **Issue**: Line 20 hardcoded path to proprietary Baymard guidelines
- **Status**: UX validation moved to private BayMAAR analysis engine
- **See**: research/baymaar-guidelines/ in BayMAAR mono-repository

---

## Documentation Consolidation

### Progress/Status Reports (Superseded)

**3. BUILD_PROGRESS.md**

- **Superseded By**: CHANGELOG.md (for version history), current README.md (for status)
- **Content**: Build progress tracking for v0.2.0 development
- **Date**: March 18, 2026

**4. COMPLETION_SUMMARY.md**

- **Superseded By**: CHANGELOG.md, README.md
- **Content**: v0.2.0 completion summary
- **Date**: March 18, 2026

**5. PROJECT_STATUS.md**

- **Superseded By**: README.md (Roadmap section), CHANGELOG.md
- **Content**: Project status and roadmap (outdated)
- **Date**: March 18, 2026

**6. IMPLEMENTATION_STATUS.md**

- **Superseded By**: CHANGELOG.md, README.md
- **Content**: Implementation status for v0.2.0
- **Date**: March 19, 2026

### Technical Analysis (Historical)

**7. CHALLENGE_ANALYSIS.md**

- **Superseded By**: Code comments and MIGRATION.md
- **Content**: Technical challenges analysis during development
- **Purpose**: Historical reference for architectural decisions
- **Date**: March 19, 2026

### Publishing Documentation (Superseded)

**8. PYPI_READINESS.md**

- **Superseded By**: Package published to PyPI (complete)
- **Content**: PyPI publishing checklist and readiness assessment
- **Status**: Package successfully published as of v0.3.0
- **Date**: March 19, 2026

**9. release-notes-v0.1.0.md**

- **Superseded By**: CHANGELOG.md (all versions)
- **Content**: Release notes for v0.1.0
- **Current Version**: v0.3.0
- **Date**: March 19, 2026

---

## What Replaced This Archive?

### Current Documentation (Active)

| Old (Archived) | New (Current) |
|----------------|---------------|
| BUILD_PROGRESS.md | [CHANGELOG.md](../CHANGELOG.md) |
| COMPLETION_SUMMARY.md | [CHANGELOG.md](../CHANGELOG.md) |
| PROJECT_STATUS.md | [README.md](../README.md) |
| IMPLEMENTATION_STATUS.md | [CHANGELOG.md](../CHANGELOG.md) |
| CHALLENGE_ANALYSIS.md | Code comments, [MIGRATION.md](../MIGRATION.md) |
| PYPI_READINESS.md | Package published (complete) |
| release-notes-v0.1.0.md | [CHANGELOG.md](../CHANGELOG.md) |
| UX_VALIDATION_INTEGRATION.md | Removed (privacy - feature moved to BayMAAR) |
| examples/ux_validation_example.py | Removed (privacy - feature moved to BayMAAR) |

### Active Documentation Files

**Core Documentation**:

- [README.md](../README.md) - Package overview, quick start, features
- [CHANGELOG.md](../CHANGELOG.md) - Version history and changes
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [LICENSE](../LICENSE) - MIT License
- [MIGRATION.md](../MIGRATION.md) - Migration guides between versions

**Publishing**:

- [PUBLISHING.md](../PUBLISHING.md) - Publishing process and guidelines

**Configuration**:

- [scrape-config.example.yaml](../scrape-config.example.yaml) - Configuration template
- [pyproject.toml](../pyproject.toml) - Package configuration
- [setup.py](../setup.py) - Package setup

---

## Privacy Compliance

### Why UX Validation Was Removed

**Timeline**:

1. **v0.1.0** (Early 2026): Package included optional UX validation against Baymard guidelines
2. **February 2026**: Privacy review identified data leak risk
3. **March 2026**: UX validation features moved to BayMAAR (private mono-repository)
4. **v0.3.0** (Current): Package is pure journey capture tool (public)

**Issue**:

- UX validation required access to proprietary Baymard Institute research data
- Baymard data includes test criteria from 20,969 site implementations (proprietary)
- Public package cannot contain or reference proprietary data

**Solution**:

```
BEFORE (v0.1.0 - WRONG):
┌──────────────────────────────┐
│ ux-journey-scraper (PUBLIC)  │
│                              │
│ ✓ Journey capture            │
│ ✓ Screenshot capture         │
│ ✗ UX validation (Baymard)    │ ← Privacy violation
└──────────────────────────────┘

AFTER (v0.3.0 - CORRECT):
┌──────────────────────────────┐     ┌─────────────────────────────┐
│ ux-journey-scraper (PUBLIC)  │     │ BayMAAR (PRIVATE)           │
│                              │     │                             │
│ ✓ Journey capture            │ ──> │ ✓ UX validation (Baymard)   │
│ ✓ Screenshot capture         │     │ ✓ Scoring system            │
│ ✓ Outputs journey.json       │     │ ✓ Research data             │
└──────────────────────────────┘     └─────────────────────────────┘
         (data coupling - safe)
```

**Current Architecture**:

- **ux-journey-scraper** (public): Pure journey capture tool
- **BayMAAR** (private): UX analysis engine with Baymard data
- **Integration**: Via data files (journey.json), not code coupling

### Remaining Optional Code

**Note**: The package still contains optional `ux_validation_enabled` parameter in `JourneyRecorder`:

- **Status**: **Safe** - Disabled by default (`ux_validation_enabled=False`)
- **Purpose**: Hook for private integration (requires external validator)
- **No Data Leak**: Does not include Baymard data or validators
- **Usage**: Only works when external validator provided (BayMAAR integration)

This is acceptable because:

1. Feature is disabled by default
2. No proprietary data is included in the package
3. No proprietary data paths are hardcoded
4. Public users cannot use it (requires BayMAAR)
5. Acts as integration hook for private mono-repository

---

## When to Reference Archived Files

### Good Reasons to Read Archive

1. **Historical Context**: Understanding development decisions
2. **Technical Challenges**: Learning from solved problems
3. **Version History**: Detailed pre-v0.2.0 development notes
4. **Architecture Evolution**: How the package evolved

### Bad Reasons to Read Archive

1. **Current Status**: Use [README.md](../README.md) and [CHANGELOG.md](../CHANGELOG.md)
2. **How to Publish**: Package already published, see [PUBLISHING.md](../PUBLISHING.md)
3. **UX Validation**: Feature removed for privacy (see BayMAAR if authorized)
4. **Implementation Guide**: Use current [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Archive Organization

**Total Files**: 9 files

**Categories**:

- **Privacy**: 2 files (UX validation docs/code)
- **Progress**: 4 files (status reports)
- **Technical**: 1 file (challenge analysis)
- **Publishing**: 2 files (readiness, release notes)

---

## Package Evolution

### Version History

**v0.1.0** (Early 2026):

- Initial release
- Manual journey recording
- Optional UX validation ⚠️ (privacy issue)

**v0.2.0** (March 2026):

- Autonomous crawling
- Config-first approach
- Enhanced capabilities
- UX validation still present ⚠️

**v0.3.0** (March 2026):

- Pure journey capture tool
- UX validation removed for privacy ✅
- Public package (safe for PyPI)

---

## References

- **Main Package**: [ux-journey-scraper on PyPI](https://pypi.org/project/ux-journey-scraper/)
- **GitHub Repository**: [resabh/ux-journey-scraper](https://github.com/resabh/ux-journey-scraper)
- **BayMAAR Mono-Repository**: Private (internal team only)
- **Baymard Institute**: [baymard.com](https://baymard.com) (research source)

---

## Data Privacy Guidelines

For the BayMAAR mono-repository, see:

- [../../DATA_PRIVACY.md](../../DATA_PRIVACY.md) - Repository-wide privacy guidelines
- [../../ARCHITECTURE.md](../../ARCHITECTURE.md) - Privacy architecture

---

**Archived**: 2026-03-20
**Reason**: Privacy compliance + documentation consolidation
**Files Archived**: 9 (2 privacy-sensitive, 7 superseded)
**Current Version**: v0.3.0 (pure journey capture)
**Privacy Status**: ✅ Compliant (no proprietary data)
