# Changelog


## Unreleased maintenance — 2026-10-07

- Hardened Neuroglancer skeleton recovery to fail closed on self-edges, invalid endpoints, disconnected graphs, cycles, and non-tree edge counts.
- Repaired the Windows camera/FlyVis launcher path construction and Python 3.12 environment handling.
- Made native `pip`/`git`/FlyVis/`dlf-flywire` launcher failures explicit instead of allowing partial execution to continue.
- Added regression coverage for the Windows launcher contract and recovery topology rejection.
- Added a bounded RTSP network-camera source, secret-safe URL provenance, CLI capture command, and regression coverage for real network-camera input.
- Added a read-only ONVIF PTZ probe with pinned `onvif-python==0.4.4`, environment-based credential handling, capability/range inspection, and regression coverage; no PTZ movement commands are issued.
- Added read-only ONVIF LAN discovery using WS-Discovery, with machine-readable discovery receipts and regression coverage; no camera movement or configuration changes are issued.


## 1.7.1 — 2026-10-05

FlyVis continuous-activity semantics guard.

- Added explicit signal semantics: continuous voltage response, arbitrary units, and no direct spike conversion.
- Added fail-closed rejection of direct FlyVis-response to `NeuralObservation` conversion until a separately evidenced encoder exists.
- Synchronized public version metadata in `ABOUT.md` and `CITATION.cff`.

## 1.7.0 — 2026-10-05

Claim-level evidence tracing release.

- Added trace_claim() to resolve a claim into its immutable evidence artifacts.
- Added the dlf-flywire claim <CLAIM_ID> command with fail-closed unknown-claim handling.
- Added regression coverage for claim tracing and CLI output.

## 1.6.0 — 2026-10-05

Validated FlyVis runtime proof release.

- Persisted a live GitHub Actions receipt for the pinned TuragaLab/FlyVis v1.2.0 model.
- Validated official FlyVis preferred-direction outputs for T4a, T4c, T5a, and T5c within the declared 45° bound.
- Hardened FlyVis source installation with immutable commit checkout and revision identity validation.
- Kept continuous model responses explicitly separate from spikes, exact FAFB-root electrical activity, camera input, Code Hand capability mapping, and biological control claims.

## 1.5.1 — 2026-10-05

Neural → Leader execution boundary release.

- Added the bounded NeuralIntentGateway and NeuralLeaderBridge path from sparse neural observations to the existing Leader TaskStep contract.
- Added deterministic observation-set hashing, fail-closed threshold/window checks, explicit permission separation, and neural-to-Code Hand integration regression coverage.
- Added a provenance-bearing FlyDrones raster adapter with pinned external-source CI integration and separate full-source/extraction fingerprints.
- Added a persisted FlyDrones end-to-end receipt proving simulator signal -> neural gateway -> Leader -> Code Hand -> Verifier execution, while explicitly excluding biological-control claims.
- Added an evidence-backed Stage B mapping for the four exact FAFB v783 T4/T5 anchor roots to subtype-level ON/OFF and canonical motion-direction properties, with machine-checkable non-claims.
- Added the executable `EvidenceBackedNeuralMapping` decoder, which stops at a functional label and fails closed on unmapped neuron identities instead of assigning agent capabilities.
- Added a bounded FlyVis response adapter and explicit model-response boundary, freezing the upstream v1.2.0 source revision and pretrained-model digest without converting continuous model responses into spike observations.
- Synchronized version, citation, release, README, and evidence metadata to 1.5.1.


## 1.5.0 — 2026-10-04

Guarded Code Hand edit release.

- Added `code.edit`, a controlled replacement operation with an exact SHA-256 precondition.
- Added atomic same-directory replacement, post-edit content hashing, stale-precondition protection, and regression coverage.
- Extended the real GitHub Actions Code Hand smoke test to create, edit, and re-test a source file through the full Policy → Capability Doctor → Execution → Verifier path.


## 1.4.0 — 2026-10-04

Code Hand foundation release.

- Added the first concrete CodeHand implementation with guarded workspace file creation and Python test execution.
- Added code.write and code.test.python capabilities to the capability doctor.
- Added explicit workspace path validation, create-only semantics, post-write SHA-256 verification, and independent run verification.
- Added dedicated Code Hand regression tests and a real GitHub Actions end-to-end smoke test that creates and tests a temporary source file and prints sealed receipts.
- Hardened the orchestrator to fail closed when a step returns a non-success execution receipt.
- Bumped the package/product version to 1.4.0.

## 1.3.1 — 2026-10-04 (maintenance)

- Re-synchronized the artifact manifest after the historical NeuRosetta lineage evidence update.
- Aligned the coordinate-pipeline regression with the current evidence wording and verified both observation forms.
- No scientific result, dataset version, or product-version semantics changed.

## 1.3.1 — 2026-10-04

Lineage regeneration reproducibility patch.

- Builder now records the canonical CSV Git blob identity used by the lineage artifact.
- Added a regression that executes the public builder and requires byte-for-byte equality with the committed 649-record lineage index.
- Preserved deterministic tuple identifiers and explicit unresolved biological compartment status.
- Synchronized package, evidence, and citation metadata to 1.3.1.


## 1.3.0 — 2026-10-04

Record-level synapse lineage release.

- Added a deterministic tuple identifier and lineage record for every one of the 649 canonical synapse-coordinate rows.
- Added fail-closed lineage validation to the provenance audit.
- Added the `lineage` CLI command.
- Added a reproducible lineage builder script and regression coverage for record-ID drift.
- Preserved the distinction between exact source corroboration and unresolved biological compartment assignment.


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
