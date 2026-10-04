# Architecture — Version 1.3.1

The project has one stable evidence chain:

source identity
→ exact dataset materialization
→ raw/committed artifact
→ deterministic transformation
→ derived artifact
→ independent validation
→ claim status
→ reproducible evidence package

## Identity

Root IDs are first-class identifiers. Approximate or nearest-neuron substitution is forbidden.

## Evidence contract

Every important scientific statement should be represented as a claim with:
- a stable claim ID;
- a classification;
- an explicit status;
- references to concrete evidence artifacts;
- caveats or unresolved boundaries where applicable.

The independent-corroboration claim for the canonical 649-row case is explicitly bound to the frozen source-receipt artifact.

The record-level lineage layer assigns each canonical tuple a stable deterministic tuple identifier and binds that record to the existing claim IDs and frozen source receipt, without introducing an unsupported biological interpretation.

## Artifact integrity

Critical evidence artifacts are bound to immutable content identities. The artifact manifest excludes itself from the hashed artifact list because a naive self-referential content hash cannot be made stable. Cross-source receipts also carry provider identity, proof workflow IDs, and proof-artifact paths. The artifact manifest registers both the lineage index and its deterministic builder. Reproducibility is additionally enforced by regenerating the lineage artifact in CI and comparing its bytes with the committed file.

## Recovery

The recovery package retrieves FAFB v783 skeletons and rejects any response whose source root ID differs from the requested ID.

## Geometry

Nearest-segment mapping is a geometric operation. It is not a biological axon/dendrite classifier.

## Packaging

The four-neuron reference circuit is stored as stable data and evidence paths. Future analyses extend these interfaces rather than creating new milestone directories.

## Scientific boundary

A reproducible coordinate or morphology mapping is not automatically a biological compartment assignment. Biological claims require independent evidence.
