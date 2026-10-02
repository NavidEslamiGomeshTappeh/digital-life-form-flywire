# Digital Life Form — FlyWire

> An auditable pipeline for turning exact FlyWire neuron IDs into reproducible circuit evidence and, eventually, biophysically usable neuron models.

## Author

**Navid Eslami Gomesh Tappeh**

This project is developed as a research-engineering effort focused on reproducible connectomics evidence and downstream neural modeling.

## The problem

FlyWire already has strong tools for data access, annotations, morphology and connectivity. This project targets the handoff between those layers:

**exact root IDs → exact identity → directed connectivity → individual synapses → exact morphology → measured geometry → downstream modeling**

The reusable output is a **Circuit Evidence Pack**: a version-pinned bundle with exact data, hashes, transformations and validation evidence.

## Current evidence: V215 → V230

Four exact anchor neurons:

| Cell | Root ID | VFB |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

V230 contains 649 coordinate rows and 75 directed pre/post pairs.

The 75 pairs are reproducibly reconstructed from the official Codex FAFB v783 connection table by selecting directed pairs incident to one of the four anchors and summing synapse counts.

The individual 649 coordinate rows are exactly reproduced from the official Codex FAFB v783 synapse_coordinates table. The historical producer script is not preserved, so the project explicitly distinguishes historical code recovery from deterministic reproduction.

## V255 — usable package

V255 makes the evidence consumable as a real package containing:

- exact four-root identity;
- pinned FlyWire annotation evidence from flyconnectome/flywire_annotations v3.2.0;
- exact V229 SWC morphology with source hashes and structural validation;
- the reproducible V254 connectivity/synapse core;
- all 649 V230 synapse rows;
- measured synapse-to-SWC centerline geometry;
- package-level source/output hashes;
- regeneration commands;
- a ZIP artifact from GitHub Actions.

The package never invents a biological compartment label. Geometry is reported as geometry.

## V256 — biological compartment evidence audit

V256 adds a source-backed cell-level polarity layer over the exact V230 synapse set.

For the 649 V230 rows:
- 331 rows have one of the four anchors as the presynaptic neuron and are classified at cell level as axon-terminal output;
- 318 rows have one of the four anchors as the postsynaptic neuron and are classified at cell level as dendritic input;
- exact coordinate-level compartment remains **UNRESOLVED**.

This distinction is deliberate. Published T4/T5 anatomy supports the cell-level input/output organization, but nearest-SWC geometry alone is not treated as proof of the biological compartment of an individual synapse.

V256 is enforced by GitHub Actions and the current audit completed with **5/5 tests passing** and the expected 649-row regression.

See `docs/V256_COMPARTMENT_EVIDENCE_AUDIT.md` and `scripts/v256_compartment_evidence_audit.py`.

## V257 — exact published dendrite provenance

V257 links all four exact anchor roots to the historical T4/T5 dendrite-analysis table used by the published morphology study.

All four exact root IDs occur once in the pinned source and are marked Dendrite_used=True:

| Cell | Root ID | Published table row | Subtype | Dendrite used |
|---|---:|---:|---|---|
| T4a | 720575940632008007 | 514 | T4a | True |
| T4c | 720575940616224414 | 2227 | T4c | True |
| T5a | 720575940625571465 | 3171 | T5a | True |
| T5c | 720575940617782941 | 4651 | T5c | True |

This is exact-root provenance, not a nearest-neuron substitution.

The published study reports extraction of T4/T5 dendritic arbors from FAFB-FlyWire. V257 establishes that the exact four project neurons were present in its historical neuron table and marked for dendrite use. It does not yet assign each V230 synapse coordinate to a specific dendrite node or segment.

See `docs/V257_PUBLISHED_DENDRITE_PROVENANCE.md` and `v257_results/V257_published_dendrite_provenance.csv`.

## What makes the project useful

The practical target is a researcher who already knows the neurons of interest and needs a trustworthy, portable model input.

The intended question is:

> Given these exact neurons and this exact FlyWire snapshot, can another researcher obtain the same circuit data and see exactly how every output was derived?

This supports circuit-hypothesis testing, fixed-connectome modeling, compartmental-model preparation, and reproducible sharing.

## What the project is not

It is not a claim to have reconstructed a complete biological fly brain.

It is also not intended to replace FlyWire/Codex access, annotation infrastructure, or whole-brain simulators. The project focuses on **exact identity + cross-layer traceability + reproducibility + simulation readiness**.

## Next scientific layer

The remaining non-trivial layer is evidence-backed biological compartment semantics. V255 deliberately leaves that unresolved until a source or validated algorithm can justify axon, dendrite, soma and related labels for each mapped synapse.

## Useful entry points

- v230_results/V230_target_synapses.csv
- v230_results/V230_validation.json
- v229_results/*.swc
- scripts/v254_build_circuit_evidence_pack.py
- scripts/v255_finalize_usable_circuit_evidence_pack.py
- scripts/test_v255_finalize_usable_circuit_evidence_pack.py
- .github/workflows/v255-usable-circuit-evidence-pack.yml
- docs/V255_USABLE_CIRCUIT_EVIDENCE_PACK.md

## Scientific status

Research engineering project. Claims are strengthened only when source data, computation and independent reproduction support them.

No open-source license is currently asserted for this repository.
