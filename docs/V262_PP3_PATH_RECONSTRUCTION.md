# V262 — PP3 path reconstruction on the exact V229 SWCs

V262 reconstructs the published PP3 dendrite-extraction path on the four exact project V229 SWCs and separates what the code proves from what remains unavailable.

## Recovered historical path

The pinned study notebook Notebooks/PP3_Dendrite_extraction.ipynb performs:

1. load a NeuRosetta Forest;
2. filter flagged trees;
3. forest.convert_forest_to_subtrees(max_workers=10);
4. save the extracted dendrite trees;
5. forest.reduce_forest(..., inplace=True);
6. save the reduced dendrite trees.

The exact four project V229 SWCs do not contain the historical .nr graph metadata, so the per-tree historical flag state is not recovered. V262 therefore reconstructs the deterministic structural operations on the exact SWCs rather than claiming execution of the missing historical forest files.

## Exact subtree selection

Pinned NeuRosetta commit:

NikDrummond/NeuRosetta@38f20f02194c129c234360db5a8be78a90c61db1

The score is:

(1 - subtree_cable / total_cable) + (subtree_leaves / total_leaves)

Branches are vertices with out_degree > 1. The maximum-scoring branch is the extracted subtree root, and all descendants of that root are retained.

Independent V262 reconstruction reproduces the checked-in V258 node IDs:

| Cell | Exact root ID | Selected node | Score |
|---|---:|---:|---:|
| T4a | 720575940632008007 | 292 | 1.132085908818 |
| T4c | 720575940616224414 | 358 | 1.145802863923 |
| T5a | 720575940625571465 | 343 | 1.168327590832 |
| T5c | 720575940617782941 | 323 | 1.292496110721 |

## Exact reduction semantics

Pinned NeuRosetta reduce_graph() defines:

- starts = branch_indices(g) and then explicitly adds the root if needed;
- stops = core_indices(g, include_root=False);
- ReduceVisitor collapses paths from a start (branch/root) to the next stop (non-root branch or leaf);
- the reduced graph keeps the original vertex coordinates and original selected root.

The crucial correction is that branch_indices() already includes the selected root, while core_indices(..., include_root=False) removes that root from the stop set. Therefore, when branch count includes the selected root:

reduced_nodes = leaves + branches

reduced_edges = leaves + branches - 1

V261 used leaves + branches + 1 and leaves + branches; that double-counted the selected root by one.

Corrected reduced counts:

| Cell | Subtree leaves | Branches including root | Reduced nodes | Reduced edges |
|---|---:|---:|---:|---:|
| T4a | 109 | 104 | 213 | 212 |
| T4c | 113 | 99 | 212 | 211 |
| T5a | 94 | 87 | 181 | 180 |
| T5c | 82 | 71 | 153 | 152 |

The reduced cable is conserved from the selected subtree because the reduction only collapses transitive nodes into path-length edges.

## Resulting PP3 root coordinates

reduce_graph() preserves the selected root vertex and its coordinate. Therefore the final reduced-tree root coordinates are:

| Cell | Root coordinate from V229/PP3, nm | Same in µm |
|---|---|---|
| T4a | (789149.7, 263182.66, 210355.22) | (789.1497, 263.18266, 210.35522) |
| T4c | (788743.8, 272949.28, 205013.56) | (788.7438, 272.94928, 205.01356) |
| T5a | (717258.25, 222005.86, 211701.61) | (717.25825, 222.00586, 211.70161) |
| T5c | (713434.3, 216064.16, 213151.64) | (713.4343, 216064.16, 213.15164) |

## Point_data comparison

The immutable published source is:

borstlab/T4_T5_Dendrite_Morphology_Paper@56901ad1853b44aeca15504cd908fa4c31009a3e

Data/Point_data.pkl

Git blob:

b85caf49f45677f2075f7b5f2c8830141cd96d02

Published coordinates are in µm.

| Cell | PP3 reduced root, µm | Point_data root, µm | Raw residual norm, µm |
|---|---|---|---:|
| T4a | (789.1497, 263.18266, 210.35522) | (-46.85120703125, 32.261150390625, -111.5519921875) | 925.119729 |
| T4c | (788.7438, 272.94928, 205.01356) | (-46.16929296875, 22.233228515625, -116.4566640625) | 929.129440 |
| T5a | (717.25825, 222.00586, 211.70161) | (11.981576171875, 50.1895, 120.4021328125) | 731.622610 |
| T5c | (713.4343, 216.06416, 213.15164) | (12.7460712890625, 54.907804687500004, 117.5732734375) | 725.307238 |

These raw residuals are deliberately marked diagnostic only. V261 established that a common coordinate frame between Point_data and V229 has not been demonstrated, so the numerical mismatch is not itself a biological or provenance failure.

## Conclusion

V262 provides an algorithmic reconstruction of the published PP3 operations that can be recovered from the pinned code and the exact V229 SWCs:

- all four published subtree roots are independently reproduced;
- reduction semantics are reconstructed without the V261 off-by-one error;
- final reduced-tree root coordinates are the selected V258/PP3 node coordinates;
- the four Point_data coordinates are provenance-linked but remain in a separate, unreconciled coordinate frame.

What remains unresolved is the exact historical .nr forest state, historical flag metadata, manual dendrite edits, a validated frame transform, and individual synapse biological compartment identity.

## CI verification

The V262 workflow downloads the immutable Point_data source, verifies its Git blob and SHA-256, reruns the PP3 reconstruction on the four exact V229 SWCs, and checks the committed machine-readable evidence.

CI validation branch created from the corrected PP3 reconstruction HEAD.
