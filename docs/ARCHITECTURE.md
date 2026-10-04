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


## Capability layer (architectural reference)

The project uses `Panniantong/Agent-Reach` as an external architectural reference for capability discovery and backend routing. The inspected main commit is `a19a171fa980a0785849596492e0af4db800c82f` (version `1.5.0` in that tree).

The useful pattern is:

`capability -> health probe -> ordered backends -> selected backend -> execution`

Our implementation must extend that with scientific controls:

`intent/policy -> capability doctor -> backend selection -> execution -> checkpoint/recovery -> artifact receipt -> independent verification -> claim`

A capability being healthy is not evidence that a scientific result is correct.

The detailed adaptation is documented in [AGENT_CAPABILITY_LAYER.md](AGENT_CAPABILITY_LAYER.md). Agent Reach is not a current V1 runtime dependency.
\n## Executable capability doctor\n\nThe first executable capability-layer component is `dlf-flywire doctor`. It performs bounded, side-effect-free probes, distinguishes missing/broken/timeout/error/healthy states, supports ordered fallback and explicit backend promotion, and isolates one capability failure from the rest of the report. It is an environment snapshot only; it is not a scientific validation result.\n\n## Execution, checkpoint, recovery, and verification\n\nThe executable runtime boundary now records each local step as a sealed execution receipt and atomically updates a per-run checkpoint before and after execution. Completed steps are resumed by receipt verification rather than re-execution. An interrupted step is replayed automatically only when the request declares itself idempotent; otherwise recovery fails closed with `RecoveryBlocked`. All process execution uses an argument vector with `shell=False`.\n\nThe verifier checks stdout/stderr digests and the receipt seal before a stored successful receipt can be trusted by higher layers. This is execution evidence, not scientific evidence.\n