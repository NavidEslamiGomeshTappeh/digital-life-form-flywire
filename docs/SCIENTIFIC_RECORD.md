# Scientific Record — Version 1.0.0

## Reference neurons

T4a 720575940632008007
T4c 720575940616224414
T5a 720575940625571465
T5c 720575940617782941

## Morphology

Four FAFB v783 SWCs were recovered through the FlyWire/fafbseg route and structurally validated. Their node counts are 880, 898, 601 and 577 respectively. The exact SHA-256 values are stored in evidence/recovery.json.

## Connectivity and synapses

The reference artifact contains 649 individual coordinate rows across 75 directed neuron pairs.

A recorded provenance execution scanned 34,156,320 rows of the official Codex FAFB v783 synapse-coordinate product and found 649 exact tuple matches, with zero missing and zero duplicate matches.

A separate connection-table proof reproduced all 75 pair counts and the total of 649 synapses from the official Codex FAFB v783 connections product.

An independent frozen Zenodo FAFB v783 analysis reproduced all 649 coordinates as component-wise midpoint mappings.

The selected pair rule is explicit: a directed pair is included when either endpoint is one of the four exact anchor roots. The observed minimum of five rows per pair is consistent with the public FAFB connectivity threshold, but the original historical extraction command is not preserved, so historical command recovery is not claimed.

## Published dendrite evidence

All four exact roots occur once in the pinned published T4/T5 neuron table and are marked Dendrite_used=True.

The published subtree-selection algorithm was independently reimplemented on the exact project SWCs. Selected branch nodes are 292, 358, 343 and 323 for T4a, T4c, T5a and T5c.

This is computational reproduction, not a direct membrane annotation.

## Point_data provenance

The historical Point_data object is preserved by immutable Git commit/blob and SHA-256 evidence. All four exact anchors occur once.

The historical binary has Git blob b85caf49f45677f2075f7b5f2c8830141cd96d02 and SHA-256 76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f.

Published study coordinates and project SWC coordinates are intentionally treated as separate frames.

## Historical generator boundary

The historical Point_data object first appeared in the study repository on 2025-12-09. The currently public PP1/PP3 preprocessing notebooks and the public NeuRosetta Forest/SWC infrastructure appeared later.

Therefore the currently public toolchain is not a complete preserved historical generator record for the December 2025 Point_data object. The original generator remains unresolved.

A dedicated GitHub Actions binary audit subsequently decoded the historical and later Point_data snapshots and selected the four project anchors by exact FAFB v783 Root ID, with one unique row per anchor in each snapshot. The historical pickle is Protocol 5 and contains 46,624 `jaxlib._jax.ArrayImpl` values across the eight PCA/angle/vector metric columns, exactly 5,828 rows × 8 columns. This is direct serialization evidence of a JAX-backed historical artifact. It still does not identify the producer code path, the exact NeuRosetta revision, or the missing Reduced_dendrites/.nr materialization.

The snapshot ledger was hardened after detecting that coordinate-nearest row selection was insufficient for 64-bit FlyWire IDs. The current evidence uses exact Root ID matching only, and the four verified IDs are 720575940632008007, 720575940616224414, 720575940625571465, and 720575940617782941. See `evidence/point_data_pickle_decode_receipt.json`.

## Biological compartment boundary

For the 649 reference rows:
- 331 rows have an anchor at the presynaptic endpoint and carry cell-level axon-terminal output semantics;
- 318 rows have an anchor at the postsynaptic endpoint and carry cell-level dendritic input semantics.

Individual synapse compartment identity remains unresolved. A centerline distance is geometry, not proof of membrane compartment.

## Evidence status vocabulary

PROVEN
REPRODUCED
INFERRED
UNRESOLVED
UNEXECUTED
UNAVAILABLE

The V1 repository never upgrades an unresolved claim because a numerical fit is visually close.
