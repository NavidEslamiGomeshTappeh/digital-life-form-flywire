# V230 exact provenance route

## Established source-level provenance

The checked-in `v230_results/V230_target_synapses.csv` contains 649 coordinate rows spanning 75 directed neuron pairs.

A GitHub Actions run on the project scanned the frozen public FlyWire FAFB v783 synapse release:

- Zenodo record: https://zenodo.org/records/10676866
- source file: `flywire_synapses_783.feather`
- frozen-file MD5: `f8f1b97c9d4b0ea9b4c8b287f6b99091`
- validation run: `37060692378`

The V241 diagnostic artifact retains every canonical pre/post coordinate for each of the same 75 pairs. An independent deterministic post-processing check then reconstructed:

`V230 (x,y,z) = ((pre_x+post_x)/2, (pre_y+post_y)/2, (pre_z+post_z)/2)`

Results:

- 649/649 V230 rows reconstruct exactly.
- 649/649 mappings are unique.
- For every one of the 75 directed pairs, the number of canonical v783 rows equals the number of V230 rows for that pair.
- Therefore the 649-row V230 file is the complete individual-synapse coordinate set for those 75 directed pairs in the frozen v783 artifact; it is not a random subset within those pairs.

This establishes deterministic source-level reconstruction from the frozen v783 synapse records.

## What the frozen source contains

The Zenodo v783 synapse table provides the presynaptic and postsynaptic root IDs plus separate XYZ coordinates for the two sides of each synapse. The reconstruction above uses those canonical pre/post points and the component-wise integer midpoint. This document does **not** call that midpoint the biological cleft center.

## Live Codex/API route

Independent public FlyWire analysis code documents the Codex per-neuron synapse-coordinate route:

`https://codex.flywire.ai/app/synapse_coordinates?root_id=<ROOT_ID>&dataset=fafb`

The public example separates `in` and `out` synapse coordinate arrays and converts the returned raw voxel coordinates with `flywire_raw2nm`.

Current Codex app pages require Google sign-in for server-side computations. That route therefore remains the correct live/API lineage to investigate, but the frozen Zenodo artifact is the reproducible public anchor used for the exact V230 reconstruction.

## Historical producer

The repository history begins with commit:

`e57b1ccc5b9f64964af223b6bf8e853579985fe0`

That commit has no parent and is the first commit containing the V230 CSV. The original historical command/script that produced the CSV is not present in Git history.

Accordingly, the evidence chain currently has two distinct parts:

1. **Proven:** V230 CSV -> deterministic midpoint reconstruction -> exact records in frozen FlyWire FAFB v783 Zenodo.
2. **Still being traced:** the historical V230 generating command and its original live/API extraction call.

## Reproduction artifacts

The V241 artifact is retained in GitHub Actions. The independent 649-row midpoint mapping used to establish the reconstruction has SHA-256:

`045183a5cbc268216c237a9708d44dd9a3ebb1d34b92e932226e7ce7e0e85d60`.

The V248 workflow independently reruns the full frozen-source scan and records source row indices and synapse IDs when available.