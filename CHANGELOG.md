# Changelog

## 1.2.2 — 2026-10-04

Claim/manifest integrity patch.

- Bound the independent-corroboration claim for the 649-row case directly to the frozen Codex/Zenodo source-receipt artifact.
- Added regression coverage that requires the artifact manifest to remain explicitly excluded from its own hashed artifact list.
- Added regression tests for claim-to-receipt binding and manifest self-exclusion.
- Synchronized package, evidence, documentation, and citation metadata to 1.2.2.


## 1.2.1 — 2026-10-04

Provenance receipt hardening patch.

- Bound each frozen cross-source receipt to a distinct proof workflow run and a committed proof artifact.
- Added provider-level and proof-run independence enforcement.
- Synchronized package/evidence/document version metadata to 1.2.1.
- Corrected stale 1.1/1.2 documentation references.


## 1.2.0 — 2026-10-04

Cross-source verification release.

- Added a machine-checkable frozen source-receipt contract for the 649-row FAFB v783 case.
- Added Codex and Zenodo provider-level independence checks and release consistency checks.
- Added `verify-sources` CLI command and integrated frozen cross-source validation into `audit`.
- Added fail-closed canonical artifact hash/row-count validation and source receipt integrity tests.
- Kept live Zenodo re-download out of the release because the archived source is approximately 9.5 GB; this release validates immutable receipts rather than pretending to perform a live re-run.


## 1.1.0 — 2026-10-04

Provenance audit engine and evidence contract release.

- Added a machine-checkable claim ledger for source observations, deterministic computations, independent corroborations, biological inferences, and unresolved boundaries.
- Added artifact-level integrity checks using SHA-256 and Git blob identities.
- Added a dedicated `dlf-flywire audit` command and integrated provenance auditing into canonical validation.
- Synchronized the canonical evidence manifest with the current semantic version.
- Removed stale V-numbered live-product labels from current evidence metadata where they could be mistaken for active product surfaces.
- Added regression coverage for evidence references, artifact integrity, status vocabulary, and version consistency.

## 1.0.1 — 2026-10-04

Security and reproducibility maintenance release.

- Removed third-party runtime dependencies from the core package.
- Removed the vulnerable `fafbseg -> diskcache` dependency chain from the default installation path.
- Replaced the live morphology recovery implementation with a direct reader for the public Neuroglancer FAFB v783 precomputed skeleton format.
- Added deterministic binary decoding, transform handling, graph orientation, SWC writing, structural validation, and malformed-input regression tests.
- Preserved the scientific evidence set and its exact morphology hashes.
- Kept GitHub Action dependencies pinned to immutable commit SHAs.

## 1.0.0 — 2026-10-04

Consolidated the entire current research state into one public Version 1 baseline.

Scientific evidence preserved:
- exact four-root FAFB v783 identity;
- 649 exact synapse rows and 75 directed pairs;
- exact public-data reproduction and independent frozen-source corroboration;
- four exact morphology artifacts and hashes;
- published dendrite inclusion evidence;
- deterministic published subtree-selection regression;
- historical Point_data provenance;
- coordinate-frame separation;
- historical generator chronology boundary;
- supporting service capability evidence.

Engineering consolidation:
- one installable Python package;
- one canonical test suite;
- one repository validation command;
- unified CI/security/release workflows;
- synchronized version metadata;
- explicit MIT license;
- version-specific scripts, workflows, result folders and root ZIP artifacts removed from the V1 working tree.

Historical Git commits remain available for forensic audit. Future development continues from 1.0.0 using normal semantic versioning rather than milestone-specific public surfaces.
