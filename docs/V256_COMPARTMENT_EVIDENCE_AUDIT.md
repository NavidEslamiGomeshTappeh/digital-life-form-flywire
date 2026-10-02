# V256 — Biological Compartment Evidence Audit

V256 is the first biological-semantics layer after the geometric mapping in V255.

## What is established

The V230 artifact contains 649 individual rows. In those rows, exactly one of the four anchor roots appears at each synapse endpoint: 331 rows have an anchor as the presynaptic neuron and 318 rows have an anchor as the postsynaptic neuron.

For the four anchor cell types:

| Cell type | Input compartment at cell level | Input neuropil | Output compartment at cell level | Output neuropil |
|---|---|---|---|---|
| T4 | dendrite | Medulla layer 10 (M10) | axon/axon terminal | Lobula Plate |
| T5 | dendrite | Lobula layer 1 (Lo1) | axon/axon terminal | Lobula Plate |

The cell-level polarity is supported by published T4/T5 anatomy and compartment-marker experiments. Drummond, Zhao & Borst (2026) describe T4 inputs in the Medulla and outputs in the Lobula Plate, T5 inputs in the Lobula and outputs in the Lobula Plate, with T4 dendrites in M10 and T5 dendrites in Lo1.

Source: https://doi.org/10.1371/journal.pcbi.1014657

Oliva et al. (2014) experimentally used dendritic and presynaptic markers to distinguish the T4/T5 dendritic projections toward Medulla/Lobula from the axonal projections in the Lobula Plate.

Source: https://doi.org/10.1186/1749-8104-9-4

## What is not established

This does **not** mean that an individual V230 x/y/z coordinate has been directly proven to lie on a dendritic or axonal compartment.

V255's nearest-SWC-centerline measurement remains a geometric measurement. V256 therefore records two separate fields:

- cell_level_compartment_inference: source-backed cell-polarity inference (dendrite or axon_terminal);
- exact_coordinate_compartment_status: deliberately UNRESOLVED.

This distinction matters because published T4/T5 FlyWire morphology work uses explicit dendrite extraction/annotation procedures rather than treating the whole reconstructed neuron as one undifferentiated compartment.

Source: https://github.com/borstlab/T4_T5_Dendrite_Morphology_Paper

## Machine-readable outputs

The audit writes:

- V256_compartment_evidence.csv — one row per V230 synapse;
- V256_compartment_evidence.json — counts, logic, source registry, and limits.

## Reproduction

    python scripts/v256_compartment_evidence_audit.py \
      --v230 v230_results/V230_target_synapses.csv \
      --output-dir v256_results

The repository regression is intentionally strict:

- 649 V230 rows must remain present;
- 331 must be presynaptic-anchor rows;
- 318 must be postsynaptic-anchor rows;
- no row may connect two anchors for this exact V230 artifact;
- no coordinate-level compartment may be promoted to PASS.

## Next unresolved scientific gate

The next real advance is not another heuristic label. It is direct evidence that associates each individual synapse coordinate with a registered neuropil/compartment representation.

The desired chain is:

exact synapse → exact coordinate → registered neuropil → compartment evidence → morphology node/segment → simulation-ready compartment

Until the registered neuropil/compartment step is independently established, V256 remains an inference layer rather than direct coordinate-level ground truth.
