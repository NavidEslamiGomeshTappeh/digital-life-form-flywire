# Consolidated Version 1 Evidence

This directory is the canonical scientific record for the public V1 baseline.

Key artifacts:
- synapses.csv — exact 649-row reference synapse artifact.
- connectivity.json — exact public connectivity reproduction.
- recovery.json — exact morphology recovery and hashes.
- dendrite_provenance.json — exact-root inclusion evidence.
- dendrite_subtree_mapping.json/csv — published algorithm regression and per-synapse geometry.
- point_data_provenance.json — immutable historical Point_data provenance.
- coordinate_provenance.json/csv — frame-aware audit.
- historical_generator_boundary.json — chronology boundary.
- claims.json — machine-checkable claim ledger for scientific statements.
- artifact_manifest.json — machine-checkable integrity fingerprints for critical artifacts.
- synapse_lineage.json — deterministic record-level lineage for all 649 canonical synapse rows.
- service_capabilities.json and live_service_evidence.json — supporting infrastructure only.
- structural_snapshot.json and structural_connectome.svg — structural reference.
- runtime_plan.json — historical resumable execution design.

These files are evidence, not a claim of a complete fly brain.

The claim ledger deliberately includes unresolved and inference-only entries. A PASS from the audit engine means the evidence contract is internally consistent and the recorded artifact identities match; it does not upgrade an unresolved biological claim.
