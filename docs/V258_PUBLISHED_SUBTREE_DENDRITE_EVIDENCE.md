# V258 — Published automatic subtree algorithm on exact project SWCs

V258 closes a reproducibility gap without pretending that an algorithmic candidate is a direct biological membrane annotation.

## What was recovered

The published T4/T5 morphology repository uses NeuRosetta in the PP3_Dendrite_extraction notebook:

1. load the full-neuron .nr forest;
2. remove trees carrying an explicit graph-level flag;
3. call forest.convert_forest_to_subtrees();
4. save the extracted dendrites;
5. reduce the forest for downstream metrics.

The historical NeuRosetta implementation scores every branch-node descendant subtree as:

(1 - subtree_cable / total_cable) + (subtree_leaves / total_leaves)

and selects the maximum-scoring branch as the root of the extracted descendant subtree.

V258 reproduces that published computational procedure on the four exact V229 SWCs already in this project.

## Exact input

The inputs are exact project artifacts:

- T4a: 720575940632008007
- T4c: 720575940616224414
- T5a: 720575940625571465
- T5c: 720575940617782941

V230 contributes the exact 649-row synapse-coordinate artifact. Every row is required to have exactly one of those four roots as an endpoint.

## What V258 produces

For each exact root, V258 records the deterministic branch node selected by the published score and the complete descendant subtree. Each incident V230 coordinate is then mapped to both:

- the nearest segment of the full SWC; and
- the nearest segment of the algorithmic subtree candidate.

This makes it possible to measure whether the original full-tree nearest segment already belongs to the candidate, without altering the source coordinate.

The checked-in CSV contains one row per V230 synapse. The JSON report contains per-cell and per-endpoint-role coverage statistics.

## Scientific meaning

A post row means the anchor is the postsynaptic neuron. V256 independently establishes dendritic-input semantics at the cell level for those rows. A pre row has cell-level axon-terminal output semantics.

V258 keeps those semantics separate. It adds a second reproducible computational layer: where the published automatic subtree procedure places each coordinate relative to its candidate dendritic arbor.

A high overlap between the full-tree nearest segment and the candidate is geometric agreement with the candidate. It is not proof that the synaptic cleft itself lies on dendritic membrane.

## Current exact result

The current regeneration contains 649 mapping rows.

The selected branch nodes are:

| Cell | Selected node | Candidate nodes |
|---|---:|---:|
| T4a | 292 | 596 |
| T4c | 358 | 570 |
| T5a | 343 | 492 |
| T5c | 323 | 362 |

Role-separated measurements are retained because output and input synapses must not be pooled when evaluating a dendrite candidate.

## Provenance

Published study repository:
borstlab/T4_T5_Dendrite_Morphology_Paper

Pinned study-code commit:
3a1aa1a2e368ff8767f40791588eaf552e6d436d

Published notebook:
Notebooks/PP3_Dendrite_extraction.ipynb

Pinned NeuRosetta implementation commit:
38f20f02194c129c234360db5a8be78a90c61db1

V229 and V230 remain the exact project-side inputs.

## Limits retained deliberately

- The internal .nr forests used in the paper are not public in the repository.
- The PP3 tree-level flag state is not encoded in the V229 SWCs.
- V229 SWCs have not been proven bitwise identical to the paper's intermediate skeleton files.
- The resulting subtree is therefore an algorithmic dendrite candidate, not a direct biological compartment annotation.
- No synaptic cleft surface or membrane mesh has been substituted for the coordinate.

## Reproduction

~~~bash
python scripts/v258_published_subtree_dendrite_evidence.py \
  --v230 v230_results/V230_target_synapses.csv \
  --morphology-dir v229_results \
  --output-dir v258_results
~~~

The CI workflow runs unit tests, regenerates the outputs, compares them byte-for-byte with the checked-in CSV/JSON, and uploads the evidence artifact.
