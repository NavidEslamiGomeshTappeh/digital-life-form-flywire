# Security Hardening Record

Version 1.0.0 applies a least-privilege and fail-closed security model for both
the scientific evidence and the software supply chain.

## Source of the hardening model

The repository was reviewed against the GitHub Security Lab
gh-secure (https://github.com/GitHubSecurityLab/gh-secure). Its current
feature model covers branch protection, private vulnerability reporting, secret
scanning with push protection, Dependabot, and CodeQL.

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

## Controls that require GitHub platform settings

The connected GitHub API used for this repository does not expose the mutation
operations required to change these repository-level security settings. They
remain explicitly tracked in issue #16 rather than being represented as
completed:

- protect main against force-push and deletion;
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

