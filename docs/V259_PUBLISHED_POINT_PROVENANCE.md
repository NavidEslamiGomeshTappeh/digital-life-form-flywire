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

A PASS means the immutable published `Point_data.pkl` was recovered, all four exact anchor IDs were present exactly once, each published root coordinate could be compared numerically with the corresponding V229 SWC, and the independently reimplemented historical NeuRosetta subtree selector agreed with the checked-in V258 selected node ID.

A PASS does `not` mean that the study's internal `.nr` tree is bitwise identical to V229, nor does it recover manual dendrite-correction decisions, nor does it assign an individual synaptic cleft to a biological membrane compartment.

## Reproducibility

The GitHub Actions workflow fetches `Point_data.pkl` from the pinned immutable commit URL in the study repository, then computes the Git blob SHA locally and requires an exact match to the pinned blob identifier. No large Zenodo archive is required for this stage.

Zenodo record 10.5281/zenodo.21876510 is the published supplementary morphology-metrics dataset associated with the study; the Git history route above is used here because the exact historical file is directly addressable by immutable commit/blob identifiers.

## Security

`Point_data.pkl` is a Python pickle. The workflow verifies both the immutable commit URL and the exact Git blob SHA before deserializing it. It is never accepted from an arbitrary user-supplied path in CI.

## Limits

- The published point data is a metric table, not the full `.nr__ topology.
- V229 morphology remains the project's exact recovered SWC set, not a proven byte-identical copy of the study's internal `.nr__ forests.
- Individual synapse cleft compartment identity is still unresolved.
