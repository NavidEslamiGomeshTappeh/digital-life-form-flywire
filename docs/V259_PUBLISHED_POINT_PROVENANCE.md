# V259 — Published Point-data provenance + algorithm regression

V259 recovers the four exact project anchor rows from the historical study-repository commit `56901ad1853b44aeca15504cd908fa4c31009a3e`, file `Data/Point_data.pkl`, and cross-checks their published root records against the exact project V229 workflow. Published coordinates are retained as source facts; they are not treated as being in the same coordinate frame as V229.

## Source chain

`borstlab/T4_T5_Dendrite_Morphology_Paper`
→ commit `56901ad1853b44aeca15504cd908fa4c31009a3e`
→ `Data/Point_data.pkl`
→ Git blob `b85caf49f45677f2075f7b5f2c8830141cd96d02`
→ four exact FlyWire IDs
→ published root coordinates (µm)
→ exact project V229 SWCs (nm) kept as a separate frame
→ historical NeuRosetta subtree root independently recomputed
→ V258 node regression.

The study's `Metrics1_Point_data.ipynb` explicitly loads the reduced dendrites and records `ID, Neuron_type, Neuron_subtype, Subtype, hemisphere, root_x, root_y, root_z`, segment count, cable, node count and branch/leaf metrics. The notebook converts the loaded reduced dendrites from nm to µm before creating these point records.

## What PASS means

A PASS means the immutable historical `Point_data.pkl` bytes were recovered from the pinned Git commit, both the Git blob SHA and SHA-256 matched exactly, all four exact anchor IDs were present exactly once, and the independently reimplemented historical NeuRosetta subtree selector agreed with the checked-in V258 selected node ID.

A PASS does **not** mean that the study's internal `.nr` tree is bitwise identical to V229, nor does it recover manual dendrite-correction decisions, nor does it assign an individual synaptic cleft to a biological membrane compartment.

## Reproducibility

V264 now recovers the binary pickle directly from the immutable historical Git commit with `git show`. It does not substitute the newer Zenodo copy when the task is historical provenance. The workflow fails closed if either the historical Git blob SHA or the SHA-256 differs.

FlyWire IDs are serialized as strings in the evidence JSON. This is deliberate: these identifiers are 64-bit integers and must never pass through IEEE-754 floating-point conversion, which can silently alter the last digits.

Zenodo record 10.5281/zenodo.21876510 remains the published supplementary morphology-metrics dataset, but it is not used as the byte-level source for this historical-anchor check.

## Security

`Point_data.pkl` is a Python pickle. The workflow verifies the immutable commit-derived bytes and exact hashes before deserializing it. It is never accepted from an arbitrary user-supplied path in CI.

## Limits

- The published point data is a metric table, not the full `.nr` topology.
- V229 morphology remains the project's exact recovered SWC set, not a proven byte-identical copy of the study's internal `.nr` forests.
- Individual synapse cleft compartment identity is still unresolved.
