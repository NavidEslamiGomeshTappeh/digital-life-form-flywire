# Security Hardening Record

Version 1.0.1 applies a least-privilege and fail-closed security model for both
the scientific evidence and the software supply chain.

## Source of the hardening model

The repository was reviewed against the GitHub Security Lab
gh-secure (https://github.com/GitHubSecurityLab/gh-secure). Its security model
covers branch protection, private vulnerability reporting, secret scanning with
push protection, Dependabot, and CodeQL.

The OpenSSF Scorecard guidance was also applied to workflow dependencies:
GitHub Actions used by the repository are pinned to immutable full-length
commit SHAs rather than mutable version tags.

## Controls implemented in the repository

- CI, security, and release workflows use least-privilege GITHUB_TOKEN permissions.
- Checkout uses persist-credentials: false.
- All GitHub Action dependencies in .github/workflows/*.yml are pinned to
  full commit SHAs, with human-readable version comments.
- CodeQL runs with the security-and-quality query suite.
- OpenSSF Scorecard runs with SARIF publication.
- Dependency Review fails closed at high severity when the GitHub Dependency
  Graph is available.
- Dependabot is configured for both Python and GitHub Actions dependencies.
- SECURITY.md defines the reporting boundary for software and scientific
  integrity issues.
- A regression test rejects workflow action references that are not pinned to
  a 40-character commit SHA.
- The core package has no third-party runtime dependencies.

## Vulnerability found and remediated

OpenSSF Scorecard on the V1.0.0 main commit reported
PYSEC-2026-2447 / CVE-2025-69872 in `diskcache`. The advisory states that
DiskCache through 5.6.3 uses Python pickle by default and can permit arbitrary
code execution when an attacker can write to the cache directory:
https://osv.dev/vulnerability/PYSEC-2026-2447

The affected package entered the recovery path through `fafbseg==3.2.2`.
FAFBseg imports `diskcache.Cache` and declares `diskcache` as a dependency.

V1.0.1 removes that dependency chain entirely. Live recovery now reads the
public FAFB v783 Neuroglancer skeleton endpoint directly using Python's standard
library and validates the decoded result before writing SWC.

The security policy is intentionally fail-closed: no claim of a fixed upstream
DiskCache release is made here.

## Controls that require GitHub platform settings

The connected GitHub API used for this repository does not expose the mutation
operations required to change these repository-level security settings. They
remain explicitly tracked in issue #16 rather than being represented as
completed:

- protect `main` against force-push/deletion;
- require CI/security status checks before merge;
- enable the GitHub Dependency Graph;
- enable or verify Dependabot alerts/security updates;
- enable or verify Secret Scanning and Push Protection;
- enable Private Vulnerability Reporting where available.

## Evidence boundary

Security configuration must not be used as evidence for a scientific claim.
Likewise, scientific provenance does not imply that GitHub platform controls
are enabled. The two evidence classes remain separate and are validated
independently.
