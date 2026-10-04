# Changelog

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
